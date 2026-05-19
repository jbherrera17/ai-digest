# Skill Folder Format

The standard for authoring skills in `.agents/skills/`. Followed by `scripts/backfill_skills.py`, the `synergi-skills-updater` Sunday cron, and the registry's content-hashing logic.

---

## The basics

**A skill is a folder.** The folder name is the skill's `slug` (e.g. `biz-finance`). Inside, one or more `.md` files describe what the skill does and how it operates.

```
.agents/skills/biz-finance/
├── SKILL.md           ← required entrypoint
├── examples.md        ← optional
└── ...
```

The folder name follows the `${department}-${name}` convention — the prefix becomes the skill's `department` field in the registry (`biz`, `exec`, `fin`, `hr`, `mkt`, `ops`, `pm`, `sales`, `sup`).

## Required and standard filenames

| Filename | Role |
|---|---|
| `SKILL.md` | **Required.** The skill's prompt. YAML frontmatter provides `name` + `description`. The body is the operating instructions the agent reads. |
| `context-assets.md` | Optional. Background context the agent needs but that doesn't fit the SKILL.md narrative — domain facts, vocabulary, references the agent draws on. |
| `examples.md` | Optional. Worked examples of inputs and outputs. |
| `formats.md` | Optional. Output format templates — tables, JSON schemas, document structures the agent should produce. |
| `instructions.md` | Optional. Additional operating rules / decision rubrics that don't belong in the core prompt. |

Other `.md` filenames are allowed but **strongly discouraged**. Stick to the standard set so reviewers, automation, and other agents know what to expect.

## Content hashing

The skill's `content_hash` (stored in `skill_registry`) is a SHA-256 over **all** `.md` files in the folder, in alphabetical order. Any change — to `SKILL.md`, to any supporting file, or adding/removing/renaming a file — produces a new hash, which lands as a `pending` version in `skill_versions` for review.

The hash input is constructed deterministically: for each `.md` file (sorted by name), the parser appends the filename, a null byte, the file's bytes, and another null byte. This means:

- Edits anywhere in any file → new hash.
- Adding a new `examples.md` → new hash.
- Renaming `context-assets.md` to `context.md` → new hash (filename is part of the input).
- Removing a file → new hash.

## Linking between skills and context

Use inline markdown links to reference other registry entries:

```markdown
See [../biz-shared/synergi-business-context.md](../biz-shared/synergi-business-context.md) for the canonical SMB economic context.
```

These links are parsed by the dependency-tracking pipeline (REQ-003). Resolution rules:

1. **Exact match** to a registry entry's `file_path` — this is how links to `*-shared` context files resolve.
2. **Walk up parent directories** — links to any file *inside* another skill's folder (e.g. `../pm-spec-writer/context-assets.md`) are attributed to that skill as a whole.

This means inside a multi-file skill, you can link from `examples.md` to your own `formats.md` without creating self-edges (the parser skips self-references).

## What stays out of the folder

- **Non-`.md` files** (templates, scripts, binary assets) are tolerated but **don't participate in the content hash** and won't be detected by the cron. If you need structured data, embed it in a fenced code block inside one of the standard `.md` files instead.
- **Subdirectories** are not supported by the registry today. Use flat folder structure only.

## Shared context folders (different pattern)

Folders named `*-shared` (e.g. `biz-shared`, `mkt-shared`) follow a **different** convention:

- They hold **shared context files** that multiple skills link to.
- **Each `.md` file inside a `*-shared` folder is registered as its own entry** (`category='context-reference'`), with its own hash and review lifecycle.
- They do NOT use rollup hashing — each file is independent.

This asymmetry is intentional: shared context is meant to be granular and individually reviewable, while a skill is conceptually a single unit that happens to be authored across multiple supporting files.

## Reference implementation

`.agents/skills/pm-spec-writer/` is the current canonical multi-file skill — it has `SKILL.md` plus `context-assets.md`. Any new multi-file skill should follow this shape.

---

## Authoring checklist

When creating a new skill:

- [ ] Folder named `${department}-${name}` in `.agents/skills/`
- [ ] `SKILL.md` with YAML frontmatter (`name`, `description`)
- [ ] Supporting files (if any) use the standard names from the table above
- [ ] Links to other skills/contexts use markdown inline format `[text](path)`
- [ ] No subdirectories, no non-`.md` content that needs versioning
- [ ] After commit: re-run `scripts/backfill_skills.py` and POST to `/api/admin/skills/sync` to land it in the registry (until Phase 5 cron handles this automatically)
