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
SOURCE_ID = "core-synergi"
SOURCE_NAME = "Synergi Core Skills"
REPO_RELATIVE_PREFIX = ".agents/skills"


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


def build_skill_entry(skill_dir: Path, scan_time: str) -> "dict | None":
    """Build a single skill registry entry. Returns None if no SKILL.md present."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return None

    slug = skill_dir.name
    department = slug.split("-", 1)[0] if "-" in slug else "general"
    content = skill_md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    description = meta.get("description", "")
    name = meta.get("name", slug)

    return {
        "id": f"{SOURCE_ID}/{slug}",
        "slug": slug,
        "name": name,
        "description": description,
        "department": department,
        "category": None,
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


def main() -> int:
    if not SKILLS_ROOT.is_dir():
        print(f"Skills root not found: {SKILLS_ROOT}", file=sys.stderr)
        return 1

    scan_time = datetime.now(timezone.utc).isoformat()

    skills: "list[dict]" = []
    skipped: "list[str]" = []
    for entry in sorted(SKILLS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        # *-shared folders hold shared context for skill prompts, not skills themselves
        if entry.name.endswith("-shared"):
            skipped.append(entry.name)
            continue
        record = build_skill_entry(entry, scan_time)
        if record is None:
            skipped.append(entry.name + " (no SKILL.md)")
            continue
        skills.append(record)

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
        "skills": skills,
    }

    json.dump(registry, sys.stdout, indent=2)
    sys.stdout.write("\n")

    # Diagnostics on stderr so stdout stays clean JSON
    print(f"# skills: {len(skills)}  sources: {len(sources)}  skipped: {len(skipped)}", file=sys.stderr)
    if skipped:
        print(f"# skipped folders: {', '.join(skipped)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
