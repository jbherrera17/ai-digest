#!/usr/bin/env python3
"""
backfill_skills.py — One-off Phase 1 backfill for REQ-001 (Skills Governance Layer).

Walks AIDevelopment/.agents/skills/, builds a JSON registry in the same shape
the synergi-skills-updater emits, and writes it to stdout. Pipe the output to
the /api/admin/skills/sync endpoint to populate the Supabase registry.

USAGE
    python3 scripts/backfill_skills.py > /tmp/skills-registry.json
    vercel curl -X POST -H "Content-Type: application/json" \
        --data @/tmp/skills-registry.json \
        https://<deployment-url>/api/admin/skills/sync

Skips *-shared folders (they hold shared context files, not skills).

Deferred to Phase 5: this script's job will eventually move into the
synergi-skills-updater repo, pointed at .agents/skills.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILLS_ROOT = Path("/Users/jbh17/Documents/AIDevelopment/.agents/skills")
REPO_ROOT = SKILLS_ROOT.parent.parent  # /Users/jbh17/Documents/AIDevelopment
SOURCE_ID = "core-synergi"
SOURCE_NAME = "Synergi Core Skills"
REPO_RELATIVE_PREFIX = ".agents/skills"

# Inline markdown link: [text](target) — captures most real-world usage.
# Group 1 = link text, group 2 = link target. Greedy on text is fine since
# brackets don't typically nest in our corpus.
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


def parse_frontmatter(text: str) -> "tuple[dict, str]":
    """Extract YAML frontmatter (between --- markers) from a SKILL.md body."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not match:
        return {}, text

    fm_raw = match.group(1)
    body = match.group(2)

    # Minimal YAML parser — handles `key: value` and quoted-string values only.
    # The SKILL.md frontmatter is uniformly simple (name + description).
    meta = {}
    for line in fm_raw.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        meta[key] = val
    return meta, body


def extract_keywords(body: str, limit: int = 12) -> "list[str]":
    """Return lowercase keywords drawn from H2/H3 headings in the markdown body."""
    headings = re.findall(r"^##+\s+(.+?)$", body, re.MULTILINE)
    words: "list[str]" = []
    seen = set()
    for h in headings:
        for w in re.findall(r"[A-Za-z][A-Za-z0-9]+", h):
            wl = w.lower()
            if len(wl) <= 2 or wl in seen:
                continue
            seen.add(wl)
            words.append(wl)
            if len(words) >= limit:
                return words
    return words


def rollup_folder_hash(skill_dir: Path) -> str:
    """Compute a deterministic SHA-256 over all .md files in a skill folder.

    Per docs/skill-folder-format.md: each .md file contributes its filename,
    a null byte, its bytes, and another null byte to the hash input, in
    alphabetical filename order. Any addition/removal/rename/edit changes
    the digest, so the Sunday cron will detect changes to any file.
    """
    h = hashlib.sha256()
    for md_file in sorted(skill_dir.glob("*.md")):
        h.update(md_file.name.encode("utf-8"))
        h.update(b"\x00")
        h.update(md_file.read_bytes())
        h.update(b"\x00")
    return h.hexdigest()


def build_skill_entry(skill_dir: Path, scan_time: str) -> "dict | None":
    """Build a single skill registry entry. Returns None if no SKILL.md present."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return None

    slug = skill_dir.name
    department = slug.split("-", 1)[0] if "-" in slug else "general"
    content = skill_md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)

    # Rollup hash covers SKILL.md PLUS any supporting files in the folder
    # (examples.md, formats.md, instructions.md, context-assets.md, ...).
    # See docs/skill-folder-format.md.
    content_hash = rollup_folder_hash(skill_dir)
    description = meta.get("description", "")
    name = meta.get("name", slug)

    return {
        "id": f"{SOURCE_ID}/{slug}",
        "slug": slug,
        "name": name,
        "description": description,
        "department": department,
        "category": "skill",
        "sourceId": SOURCE_ID,
        "sourceType": "synergi-original",       # v2: explicit
        "scope": "domain-generic",              # v2: per PRD §10 default for the 74
        "filePath": f"{REPO_RELATIVE_PREFIX}/{slug}",
        "upstreamUrl": None,
        "author": {"name": "Synergi AI"},
        "license": "proprietary",
        "originalPath": f"{slug}/SKILL.md",     # legacy field, harmless
        "currentVersion": "1.0.0",
        "versions": [
            {
                "version": "1.0.0",
                "changedAt": scan_time,
                "changeType": "initial",
                "contentHash": content_hash,
            }
        ],
        "isExpertSkill": False,                 # legacy boolean (still read by upsert fallback)
        "isCoreSkill": True,                    # legacy boolean
        "hasCommand": False,
        "keywords": extract_keywords(body),
        "discoveredAt": scan_time,
        "lastCheckedAt": scan_time,
    }


def _first_paragraph(body: str) -> str:
    """Return the first non-heading paragraph from a markdown body, trimmed."""
    for chunk in re.split(r"\n\s*\n", body.strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Skip pure-heading chunks
        if all(line.lstrip().startswith("#") for line in chunk.splitlines()):
            continue
        # Strip leading heading lines from a mixed chunk
        lines = [ln for ln in chunk.splitlines() if not ln.lstrip().startswith("#")]
        text = " ".join(ln.strip() for ln in lines if ln.strip())
        if text:
            return text[:300]
    return ""


def _source_files_for_entry(entry: dict) -> list:
    """Return the list of source files to scan for links.

    Skills: all .md files in the folder (rollup behavior per the
    multi-file convention in docs/skill-folder-format.md).
    Context-references: the single .md file the entry points at.
    """
    fp = entry["filePath"]
    abs_path = REPO_ROOT / fp
    if entry.get("category") == "context-reference":
        return [abs_path] if abs_path.is_file() else []
    if not abs_path.is_dir():
        return []
    return sorted(abs_path.glob("*.md"))


def extract_dependencies(entry: dict, path_to_skill_id: dict) -> list:
    """Parse inline markdown links from this entry's source file(s).

    For skills, walks all .md files in the folder and dedupes across them —
    a single edge per (source skill, target skill) regardless of which
    supporting file produced the link.

    Resolution rules (REQ-003 §10 + multi-file convention):
      - Exact path match against registry file_path values
      - Walk up parent directories — files inside a skill folder attribute
        to the skill as a whole
      - External URLs, anchors, non-.md targets skipped
      - Self-references skipped
    """
    source_files = _source_files_for_entry(entry)
    if not source_files:
        return []

    edges = []
    seen = set()

    for source_file in source_files:
        try:
            content = source_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        edges.extend(_parse_links_from_content(content, source_file, entry, path_to_skill_id, seen))

    return edges


def _parse_links_from_content(content: str, source_file: Path, entry: dict, path_to_skill_id: dict, seen: set) -> list:
    """Extract dependency edges from a single source file's content.

    `seen` is mutated to dedupe (source_id, target_id) pairs across files.
    """
    edges = []
    for match in LINK_RE.finditer(content):
        link_text = match.group(1).strip()
        link_target = match.group(2).strip()

        # Skip external schemes and pure anchors
        if link_target.startswith(("http://", "https://", "mailto:", "ftp://", "#")):
            continue
        # Strip query/fragment
        link_path = link_target.split("#", 1)[0].split("?", 1)[0]
        if not link_path:
            continue
        # Only consider markdown targets
        if not link_path.endswith(".md"):
            continue

        # Resolve relative to the source file's directory
        try:
            resolved = (source_file.parent / link_path).resolve()
            repo_rel = str(resolved.relative_to(REPO_ROOT))
        except (ValueError, OSError):
            continue  # outside REPO_ROOT or unresolvable

        # Match against registry:
        #   1. Exact path match (covers context-references whose file_path is the .md file)
        #   2. Walk up parent directories — covers skill folders whose file_path is the
        #      folder (e.g. link to pm-spec-writer/SKILL.md OR pm-spec-writer/context-assets.md
        #      both resolve to the pm-spec-writer skill folder).
        matched_id = path_to_skill_id.get(repo_rel)
        if not matched_id:
            parts = repo_rel.split("/")
            while len(parts) > 1:
                parts.pop()
                candidate = "/".join(parts)
                # Don't escape above .agents/skills
                if not candidate.startswith(REPO_RELATIVE_PREFIX):
                    break
                matched_id = path_to_skill_id.get(candidate)
                if matched_id:
                    break

        if not matched_id:
            print(
                f"# unresolved link in {entry['id']}: '{link_target}' -> {repo_rel}",
                file=sys.stderr,
            )
            continue

        # Skip self-references
        if matched_id == entry["id"]:
            continue

        # Deduplicate (same entry might link to the same target multiple times)
        key = (entry["id"], matched_id)
        if key in seen:
            continue
        seen.add(key)

        edges.append({
            "skillId": entry["id"],
            "dependsOnId": matched_id,
            "linkText": link_target,
            "linkTarget": repo_rel,
            "linkKind": "inline-markdown",
        })

    return edges


def build_context_entries(shared_dir: Path, scan_time: str) -> list:
    """Build registry entries for shared-context files inside a *-shared folder.

    These are markdown files that skills link to (e.g.
    biz-shared/synergi-business-context.md). They are distinct from skills —
    no YAML frontmatter, no role definition — but they still need governance
    because skill behavior depends on them. Tagged category='context-reference'.
    """
    if not shared_dir.name.endswith("-shared"):
        return []

    department = shared_dir.name.rsplit("-shared", 1)[0]
    entries = []
    for md_file in sorted(shared_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        stem = md_file.stem  # filename without extension

        # Unique slug across folder + file (multiple files per shared folder allowed)
        slug = f"{shared_dir.name}-{stem}"
        name = stem.replace("-", " ").replace("_", " ").title()
        description = _first_paragraph(content) or f"Shared {department} context referenced by {department}-* skills."

        entries.append({
            "id": f"{SOURCE_ID}/{slug}",
            "slug": slug,
            "name": name,
            "description": description,
            "department": department,
            "category": "context-reference",
            "sourceId": SOURCE_ID,
            "sourceType": "synergi-original",
            "scope": "domain-generic",
            "filePath": f"{REPO_RELATIVE_PREFIX}/{shared_dir.name}/{md_file.name}",
            "upstreamUrl": None,
            "author": {"name": "Synergi AI"},
            "license": "proprietary",
            "originalPath": f"{shared_dir.name}/{md_file.name}",
            "currentVersion": "1.0.0",
            "versions": [
                {
                    "version": "1.0.0",
                    "changedAt": scan_time,
                    "changeType": "initial",
                    "contentHash": content_hash,
                }
            ],
            "isExpertSkill": False,
            "isCoreSkill": True,
            "hasCommand": False,
            "keywords": [],
            "discoveredAt": scan_time,
            "lastCheckedAt": scan_time,
        })
    return entries


def main() -> int:
    if not SKILLS_ROOT.is_dir():
        print(f"Skills root not found: {SKILLS_ROOT}", file=sys.stderr)
        return 1

    scan_time = datetime.now(timezone.utc).isoformat()

    skills: "list[dict]" = []
    context_entries: "list[dict]" = []
    skipped: "list[str]" = []
    for entry in sorted(SKILLS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.endswith("-shared"):
            # Shared context files — different category, same registry table
            shared_records = build_context_entries(entry, scan_time)
            if not shared_records:
                skipped.append(entry.name + " (no .md files)")
                continue
            context_entries.extend(shared_records)
            continue
        record = build_skill_entry(entry, scan_time)
        if record is None:
            skipped.append(entry.name + " (no SKILL.md)")
            continue
        skills.append(record)

    # Combine skills + context entries — both go into skill_registry,
    # the category field distinguishes them.
    all_entries = skills + context_entries

    # Build path -> skill_id map for dependency resolution (REQ-003 Phase 2)
    path_to_skill_id = {e["filePath"]: e["id"] for e in all_entries}

    # Parse markdown links from each entry's source file and emit edges
    dependencies = []
    for entry in all_entries:
        dependencies.extend(extract_dependencies(entry, path_to_skill_id))

    sources = [
        {
            "id": SOURCE_ID,
            "type": "core",
            "name": SOURCE_NAME,
            "author": {"name": "Synergi AI"},
            "license": "proprietary",
            "localPath": str(SKILLS_ROOT),
            "department": "multi",
            "lastScannedAt": scan_time,
        }
    ]

    registry = {
        "version": "2.0.0",
        "generatedAt": scan_time,
        "generatedBy": "ai-tools/scripts/backfill_skills.py",
        "sources": sources,
        "skills": all_entries,
        "dependencies": dependencies,
    }

    json.dump(registry, sys.stdout, indent=2)
    sys.stdout.write("\n")

    # Diagnostics on stderr so stdout stays clean JSON
    print(
        f"# skills: {len(skills)}  context-references: {len(context_entries)}  "
        f"dependencies: {len(dependencies)}  "
        f"sources: {len(sources)}  skipped: {len(skipped)}",
        file=sys.stderr,
    )
    if skipped:
        print(f"# skipped folders: {', '.join(skipped)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
