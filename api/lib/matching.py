"""Skill matching engine — REQ-001 Phase 2.

Heuristic-only (no LLM). Given a set of incoming skills and the current
registry, produce match suggestions that land in skill_matches with
review_status='pending' for curator review.

Match types:
  'duplicate'   — Identical content hash, different skill_id
                  (same skill ingested under a different source key)
  'new_version' — Same slug, different skill_id (re-importing under
                  a new source name) or otherwise strong signal that
                  this is a re-versioning of an existing entry
  'similar'     — High keyword overlap, plausible candidate to merge
                  or reclassify; reviewer decides

Operates on the *result* of an upsert: candidate skills have already been
inserted into skill_registry, and we have a skill_id_map (text id -> UUID)
covering every entry. The matcher compares new/changed incoming entries
against the rest of the registry and emits match records.
"""

from collections import Counter

# Tuning knobs — conservative defaults, adjust after observing real cron traffic.
KEYWORD_JACCARD_THRESHOLD = 0.40   # Min overlap to emit a 'similar' match
SAME_DEPT_BOOST = 0.10             # Confidence add when candidate + match share a department
MAX_MATCHES_PER_CANDIDATE = 3      # Cap to avoid flooding the review queue


def keyword_jaccard(a, b):
    """Jaccard similarity of two keyword lists (case-insensitive set comparison)."""
    set_a = {k.lower() for k in (a or [])}
    set_b = {k.lower() for k in (b or [])}
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def _find_matches_for(candidate, existing_skills):
    """For one incoming candidate, score every existing entry; return top matches.

    Returns a list of dicts with keys: existing, match_type, confidence, reasoning.
    Sorted by confidence descending. Limited to MAX_MATCHES_PER_CANDIDATE.
    Empty list if no candidate scores above thresholds.
    """
    candidate_id = candidate.get('id') or candidate.get('skill_id')
    candidate_slug = candidate.get('slug')
    candidate_hash = (candidate.get('versions', [{}])[-1].get('contentHash')
                      if candidate.get('versions') else candidate.get('content_hash'))
    candidate_dept = candidate.get('department')
    candidate_keywords = candidate.get('keywords') or []

    scored = []
    for existing in existing_skills:
        existing_id = existing.get('skill_id')
        if existing_id == candidate_id:
            continue  # Same skill — upsert handles versioning, no match needed
        existing_slug = existing.get('slug')
        existing_hash = existing.get('content_hash')
        existing_dept = existing.get('department')
        existing_keywords = existing.get('keywords') or []

        # Rule 1 — Exact content hash match across different IDs = duplicate
        if candidate_hash and existing_hash and candidate_hash == existing_hash:
            scored.append({
                'existing': existing,
                'match_type': 'duplicate',
                'confidence': 1.0,
                'reasoning': f"Identical content hash ({existing_hash[:12]}...)",
            })
            continue

        # Rule 2 — Same slug across different IDs = re-import under new source
        if candidate_slug and candidate_slug == existing_slug:
            scored.append({
                'existing': existing,
                'match_type': 'new_version',
                'confidence': 0.95,
                'reasoning': f"Same slug '{candidate_slug}' under a different skill_id",
            })
            continue

        # Rule 3 — Keyword overlap above threshold
        jaccard = keyword_jaccard(candidate_keywords, existing_keywords)
        if jaccard >= KEYWORD_JACCARD_THRESHOLD:
            confidence = jaccard
            reasoning_bits = [f"Keyword Jaccard {jaccard:.2f}"]
            if candidate_dept and candidate_dept == existing_dept:
                confidence = min(0.94, confidence + SAME_DEPT_BOOST)  # cap below 0.95 (reserved for slug/hash rules)
                reasoning_bits.append(f"same department '{candidate_dept}'")
            scored.append({
                'existing': existing,
                'match_type': 'similar',
                'confidence': round(confidence, 4),
                'reasoning': ', '.join(reasoning_bits),
            })

    scored.sort(key=lambda m: m['confidence'], reverse=True)
    return scored[:MAX_MATCHES_PER_CANDIDATE]


def compute_match_suggestions(incoming_skills, existing_skills, skill_id_map):
    """Produce match records keyed by UUID, ready for upsert_skill_matches.

    incoming_skills: list of skill JSON entries from the sync payload.
    existing_skills: list of dicts from get_all_skills() (already includes any
                     just-upserted entries since this runs *after* skill upsert).
    skill_id_map:    {text skill_id -> UUID} covering every entry.

    Returns a list of dicts shaped for upsert_skill_matches v2 path:
      {candidateSkillId, matchedSkillId, matchType, confidence, reasoning}
    candidateSkillId / matchedSkillId are UUIDs.
    """
    suggestions = []
    for candidate in incoming_skills:
        candidate_text_id = candidate.get('id')
        candidate_uuid = skill_id_map.get(candidate_text_id)
        if not candidate_uuid:
            continue  # Couldn't resolve to a registry row — skip

        matches = _find_matches_for(candidate, existing_skills)
        for m in matches:
            matched_uuid = skill_id_map.get(m['existing']['skill_id'])
            if not matched_uuid or matched_uuid == candidate_uuid:
                continue
            suggestions.append({
                'candidateSkillId': candidate_uuid,
                'matchedSkillId': matched_uuid,
                'matchType': m['match_type'],
                'confidence': m['confidence'],
                'reasoning': m['reasoning'],
            })
    return suggestions


# ── Self-test (run with: python3 -m api.lib.matching) ──
if __name__ == '__main__':
    # Synthetic registry: 3 existing skills
    existing = [
        {'skill_id': 'src-a/biz-finance', 'slug': 'biz-finance',
         'department': 'biz', 'content_hash': 'aaa',
         'keywords': ['finance', 'modeling', 'budget', 'roi', 'cashflow']},
        {'skill_id': 'src-a/biz-pricing', 'slug': 'biz-pricing',
         'department': 'biz', 'content_hash': 'bbb',
         'keywords': ['pricing', 'margin', 'tier', 'discount']},
        {'skill_id': 'src-a/mkt-launch', 'slug': 'mkt-launch',
         'department': 'mkt', 'content_hash': 'ccc',
         'keywords': ['launch', 'campaign', 'gtm']},
    ]
    # Each text ID must map to a unique fake UUID (mirrors real Supabase IDs).
    skill_id_map = {s['skill_id']: f"uuid-{s['skill_id'].replace('/', '-')}" for s in existing}

    # Candidates: a duplicate, a slug-clash, a keyword-overlap, and a no-match
    candidates = [
        {'id': 'src-b/biz-finance-dup', 'slug': 'biz-finance-dup',
         'department': 'biz', 'keywords': ['finance', 'modeling'],
         'versions': [{'contentHash': 'aaa'}]},                  # → duplicate(biz-finance)
        {'id': 'src-c/biz-finance', 'slug': 'biz-finance',
         'department': 'biz', 'keywords': ['finance', 'kpi'],
         'versions': [{'contentHash': 'zzz'}]},                  # → new_version(biz-finance) — same slug
        {'id': 'src-b/biz-money',  'slug': 'biz-money',
         'department': 'biz', 'keywords': ['finance', 'budget', 'roi'],
         'versions': [{'contentHash': 'ddd'}]},                  # → similar(biz-finance) — keyword overlap + same dept
        {'id': 'src-b/whatever',   'slug': 'whatever',
         'department': 'biz', 'keywords': ['unrelated', 'topic'],
         'versions': [{'contentHash': 'eee'}]},                  # → no match
    ]
    for c in candidates:
        skill_id_map[c['id']] = f"uuid-{c['id'].replace('/', '-')}"

    suggestions = compute_match_suggestions(candidates, existing, skill_id_map)

    by_candidate = {}
    for s in suggestions:
        by_candidate.setdefault(s['candidateSkillId'], []).append(s)

    print(f"{len(suggestions)} match suggestions produced.\n")
    for cand, matches in by_candidate.items():
        print(f"  candidate {cand}")
        for m in matches:
            print(f"    -> {m['matchedSkillId']:30} ({m['matchType']}, "
                  f"conf={m['confidence']:.2f}) {m['reasoning']}")

    # Assertions
    assert any(s['matchType'] == 'duplicate' and s['confidence'] == 1.0 for s in suggestions), \
        "Expected at least one duplicate match"
    assert any(s['matchType'] == 'new_version' and s['confidence'] == 0.95 for s in suggestions), \
        "Expected at least one new_version match (slug clash)"
    assert any(s['matchType'] == 'similar' for s in suggestions), \
        "Expected at least one similar match"
    no_match_uuid = 'uuid-src-b-whatever'
    assert no_match_uuid not in by_candidate, "Unrelated candidate should produce no matches"
    print("\nAll assertions passed.")
