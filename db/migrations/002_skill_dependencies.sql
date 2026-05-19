-- ============================================
-- Migration 002 — Skill Dependency Tracking
-- Per REQ-003: ai-tools/requests/REQ-003-skill-dependency-tracking.md
-- (REQ originally drafted as REQ-002; renumbered to REQ-003 on 2026-05-19
--  to avoid collision with REQ-002 higgins2-chat-artifacts. Migration file
--  number is independent and stays at 002 — sequential order of DB changes.)
--
-- Purely additive — no changes to existing tables. Safe to apply
-- against the live REQ-001 schema (skill_registry already has 74 rows).
-- Run in Supabase SQL Editor or via psql.
--
-- After applying, also reflected in db/skills_schema.sql as the
-- canonical "fresh-start" representation of the current schema state.
-- ============================================

-- Re-runnable: idempotent on its own.
DROP VIEW IF EXISTS skill_dependent_count CASCADE;
DROP VIEW IF EXISTS skill_dependency_graph CASCADE;
DROP TABLE IF EXISTS skill_dependencies CASCADE;

-- ── skill_dependencies ───────────────────────────────────────────
CREATE TABLE skill_dependencies (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- The dependent (e.g. biz-finance)
  skill_id UUID NOT NULL REFERENCES skill_registry(id) ON DELETE CASCADE,

  -- What it depends on (e.g. the biz-shared context entry)
  depends_on_id UUID NOT NULL REFERENCES skill_registry(id) ON DELETE CASCADE,

  -- The raw link as it appears in the source file
  link_text TEXT,                           -- e.g. "biz-shared/synergi-business-context.md"
  link_target TEXT,                         -- resolved repo-relative path

  -- 'inline-markdown' for v1; reserved values for future kinds
  link_kind TEXT NOT NULL DEFAULT 'inline-markdown',

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

-- ── Helper views ─────────────────────────────────────────────────
-- skill_dependency_graph: one row per edge, joined with both ends' metadata.
-- Drives "what does this skill depend on" / "what depends on this skill" UI.
CREATE VIEW skill_dependency_graph AS
SELECT
  d.id                    AS edge_id,
  d.skill_id,
  s.slug                  AS skill_slug,
  s.name                  AS skill_name,
  s.department            AS skill_department,
  d.depends_on_id,
  t.slug                  AS depends_on_slug,
  t.name                  AS depends_on_name,
  t.department            AS depends_on_department,
  t.category              AS depends_on_category,
  d.link_kind,
  d.link_text,
  d.link_target,
  d.resolved_at
FROM skill_dependencies d
JOIN skill_registry s ON s.id = d.skill_id
JOIN skill_registry t ON t.id = d.depends_on_id;

-- skill_dependent_count: how many things depend on each entry.
-- Drives the "blast radius" indicator on review surfaces.
CREATE VIEW skill_dependent_count AS
SELECT
  d.depends_on_id,
  COUNT(*) AS dependent_count
FROM skill_dependencies d
GROUP BY d.depends_on_id;
