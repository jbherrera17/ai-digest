# REQ-003 — Skill Dependency Tracking

> _Renumbered from REQ-002 → REQ-003 on 2026-05-19. REQ-002 is reserved for `higgins2-chat-artifacts`._

**Owner:** JB Herrera
**Drafted by:** Higgins
**Date:** 2026-05-19
**Status:** Approved — decisions closed 2026-05-19
**Depends on:** REQ-001 Phase 1 (complete — schema + 74 entries live in production)
**Project:** ai-tools/skills + synergi-skills-updater + AIDevelopment/.agents/skills

---

## 1. Problem

The skills in `.agents/skills/` reference each other and reference shared context files via relative-path markdown links. For example, `biz-finance/SKILL.md` contains:

```
[../biz-shared/synergi-business-context.md](../biz-shared/synergi-business-context.md)
```

When `biz-shared/synergi-business-context.md` changes, every skill that links to it is effectively a new version — its referenced material has shifted. But the registry doesn't know this. The Sunday cron only sees the changed file in isolation; it can't tell the curator "this single change affects 8 other skills."

REQ-001's Phase 1 backfill registered the 8 shared context files as `category='context-reference'` so the cron will detect their changes. **REQ-003 closes the second half of that loop: make the dependency graph explicit, so a review of one entry knows what else it touches.**

## 2. Strategic intent

The Sunday review ritual is part of Synergi's curator-as-moat position (REQ-001 §2). For that ritual to scale, the curator needs to see the **blast radius** of a proposed change, not just the change itself. Dependency tracking turns the registry from a flat list into a reviewable graph — a structural enabler for the >90-second-per-skill review target.

## 3. Users

| User | Job-to-be-done | Frequency |
|---|---|---|
| **Curator-JB** | At review time, see "approving this version will affect N other entries — review them too." | Weekly |
| **Higgins 2.0** | Resolve a skill's links to live registry entries (not raw filesystem paths) — including in environments where the file tree isn't accessible. | Per agent invocation |
| **Future v2+: Matching engine (Phase 2 of REQ-001)** | Use dependency overlap as a signal for "is this candidate a new version of X or a brand-new skill?" | Per cron run |

Same audience as REQ-001 — no new users.

## 4. Goals & success metrics

| Goal | Metric | Target |
|---|---|---|
| Every existing skill's dependencies are mapped | Edges captured / links present in SKILL.md content | ≥ 95% |
| Reviewers see impact at review time | Curator can answer "what else does this change touch?" in one query | 1 query |
| Dependency data stays fresh | Stale edges purged on every sync | 100% |
| API returns dependency graph | `/api/skills/<id>/dependencies` and `/api/skills/<id>/dependents` both work | Both endpoints live |

## 5. In scope (v1)

1. New `skill_dependencies` table (schema in §8).
2. Backfill script extension: parse markdown links in each entry's source file, resolve to registry rows, emit edges.
3. Upsert helper + idempotent re-sync (every cron run re-derives all edges for changed entries).
4. Two read API endpoints:
   - `GET /api/skills/<skill_id>/dependencies` — what does this entry depend on?
   - `GET /api/skills/<skill_id>/dependents` — what depends on this entry?
5. Two convenience views (`skill_dependency_graph`, `skill_dependent_count`) for the curator UI.

## 6. Out of scope (v2+)

- **Auto-cascade reviews.** When B changes, NOT automatically marking dependent A as `pending`. Reviewer sees the impact and decides; the system never silently re-opens approved versions.
- **Multi-hop impact analysis.** If A → B → C, changing C only surfaces B as directly affected. Transitive reach can be computed at query time on existing edges if needed; not baked into the table.
- **Reference-style markdown links** (`[text][ref]` + `[ref]: path` block). Inline-only for v1; reference-style is rare in the current corpus.
- **External URLs and HTTP links.** Not registry dependencies, skipped.
- **Dependency surfacing in `/skills.html` UI.** That's Phase 3 of REQ-001 (curator UX polish). REQ-003 ships the data; UI consumes it later.
- **Cross-source dependencies** (a Synergi-original linking to a pm-skills passthrough). Resolves the same way; just noted that the table can hold heterogeneous source pairs.

## 7. MVP cut

Two things must both be true:

1. **Edges exist.** After the next backfill run, the `skill_dependencies` table contains every parseable link from every SKILL.md and every context-reference markdown file in the registry.
2. **API works.** `GET /api/skills/<id>/dependencies` and `/dependents` return correct lists, with one query each (no client-side joins).

Definition of "correct": every `[text](../something.md)` style link in a registry entry's source file that resolves to another registry entry produces exactly one edge row. Broken links and external URLs produce zero rows (and are logged).

## 8. Schema delta

**Additive only — no changes to existing tables.**

```sql
CREATE TABLE skill_dependencies (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- The dependent (e.g. biz-finance)
  skill_id UUID NOT NULL REFERENCES skill_registry(id) ON DELETE CASCADE,

  -- What it depends on (e.g. biz-shared-synergi-business-context)
  depends_on_id UUID NOT NULL REFERENCES skill_registry(id) ON DELETE CASCADE,

  -- The raw link as it appears in the source file
  link_text TEXT,                           -- e.g. "biz-shared/synergi-business-context.md"
  link_target TEXT,                         -- resolved repo-relative path

  -- What kind of dependency this is (for filtering)
  link_kind TEXT NOT NULL DEFAULT 'inline-markdown',
                                            -- 'inline-markdown' | 'reference-markdown' (v2)

  resolved_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),

  UNIQUE(skill_id, depends_on_id)
);

CREATE INDEX idx_skill_deps_skill      ON skill_dependencies(skill_id);
CREATE INDEX idx_skill_deps_depends_on ON skill_dependencies(depends_on_id);

ALTER TABLE skill_dependencies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read skill_dependencies"
  ON skill_dependencies FOR SELECT USING (true);
CREATE POLICY "Service full access skill_dependencies"
  ON skill_dependencies FOR ALL USING (true);

CREATE TRIGGER skill_dependencies_updated_at
  BEFORE UPDATE ON skill_dependencies
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

Plus two helper views:

```sql
CREATE VIEW skill_dependency_graph AS
SELECT
  d.skill_id,
  s.slug         AS skill_slug,
  s.name         AS skill_name,
  d.depends_on_id,
  t.slug         AS depends_on_slug,
  t.name         AS depends_on_name,
  t.category     AS depends_on_category,
  d.link_kind,
  d.link_text
FROM skill_dependencies d
JOIN skill_registry s ON s.id = d.skill_id
JOIN skill_registry t ON t.id = d.depends_on_id;

CREATE VIEW skill_dependent_count AS
SELECT
  d.depends_on_id,
  COUNT(*) AS dependent_count
FROM skill_dependencies d
GROUP BY d.depends_on_id;
```

## 9. Phased delivery plan

| Phase | Deliverable | Estimated effort |
|---|---|---|
| **0 — Prereqs** | Confirm REQ-001 Phase 1 still healthy (it is). Confirm open decisions in §10. | 1 short session |
| **1 — Schema** | Apply `skill_dependencies` table + views to production Supabase. | 1 session |
| **2 — Parser** | Extend `scripts/backfill_skills.py` to parse inline markdown links per registry entry. Resolve relative paths to slugs. Emit edges in registry JSON. | 1 session |
| **3 — Upsert** | Add `upsert_skill_dependencies()` to `api/lib/supabase.py`. Wire into `/api/admin/skills/sync`. | 1 session |
| **4 — Read API** | Add `GET /api/skills/<id>/dependencies` and `/dependents` endpoints. | 1 session |
| **5 — Re-run** | Re-run backfill against production; verify edges land cleanly. | 0.5 session |

Total: **4–5 working sessions** end-to-end.

## 10. Decisions (closed 2026-05-19)

All five resolved per JB's approval of the original recommendations:

1. **Edge direction = `A → B` means "A depends on B."** Standard DAG convention. The dependent owns the edge.

2. **Stale-edge handling = DELETE + re-INSERT** per re-scanned entry. Idempotent; the table never accumulates phantom edges from old link versions.

3. **Auto-cascade = NO.** When B changes, dependent A is NOT silently marked `pending`. The reviewer sees the impact via the dependency graph and decides whether to re-open A. Silent cascades would corrupt review-queue semantics.

4. **Link kinds = inline markdown only** for v1. `[text](path)` patterns. Reference-style (`[ref]: path`) and HTML `<a href>` deferred — near-zero corpus benefit for parser complexity.

5. **Path resolution = exact `file_path` match.** A link's resolved repo-relative path must match a registry entry's `file_path` exactly. No fuzzy / by-name resolution. Unresolved links logged to stderr but do not fail the sync.

## 11. Risks

| Risk | Mitigation |
|---|---|
| Link parser misses non-standard markdown patterns | Start strict, log unresolved links in stderr during backfill, expand parser if real corpus has cases. |
| Re-derived edges on every sync wastes I/O for unchanged entries | Phase 2 of REQ-001 (matching engine) will surface "did this entry change since last scan." Until then, re-derive all edges every run — cost is low (single-digit milliseconds per entry). |
| File path resolution fails when files are moved | Backfill logs every unresolved link; curator sees broken-link warnings at review time. Acceptable v1 behavior. |
| Bidirectional FK CASCADE can mass-delete edges if a registry row is removed | Intended behavior — if a skill is deleted from the registry, its edges become invalid. CASCADE is correct here. |

## 12. Dependencies

- **REQ-001 Phase 1 live** (it is — 74 entries in production as of 2026-05-18).
- `update_updated_at()` function exists in Supabase (already present per REQ-001 v2 schema).
- `scripts/backfill_skills.py` extensible (it is — Phase 2 just adds a link-parsing pass per entry).

## 13. Definition of done (v1)

- [ ] `skill_dependencies` table + 2 views applied to production.
- [ ] `scripts/backfill_skills.py` parses inline markdown links and emits edges.
- [ ] `upsert_skill_dependencies()` callable from the sync handler.
- [ ] `/api/skills/<id>/dependencies` and `/api/skills/<id>/dependents` both return correct lists.
- [ ] Re-run backfill against production; `SELECT count(*) FROM skill_dependencies` is non-zero and `≥ 8` (since all 8 *-shared files have dependent skills).
- [ ] Re-run is idempotent — running twice produces the same edge count.
- [ ] Unresolved links logged but don't fail the sync.
- [ ] This REQ moved to `requests/archive/` with a one-line completion stamp.

---

## Appendix A — Why this matters for REQ-001's success metrics

REQ-001 §4 set a curator review target of <90 seconds per skill. Without dependency tracking, that target is unachievable: a reviewer can't validate a `biz-shared` change in <90s if they don't know it affects 8 other skills. REQ-003 is the structural enabler.

## Appendix B — Expected edge count after first run

From the source corpus, we expect roughly:
- Every biz-* skill links to `biz-shared/synergi-business-context.md` → ~8 edges
- Every fin-* skill links to `fin-shared/synergi-finance-context.md` → ~6 edges
- Similar density for mkt, hr, ops, sales, sup, exec
- Plus occasional cross-skill links (e.g. biz-finance referencing biz-pricing)

Total expected: **60–100 edges** for the current 74-entry registry.
