-- Skills Registry Tables
-- Run in Supabase SQL Editor after the main schema.sql

-- ============================================
-- SKILL SOURCES TABLE
-- ============================================
CREATE TABLE skill_sources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('core', 'expert-repo')),
  author_name TEXT,
  author_email TEXT,
  author_url TEXT,
  license TEXT,
  repo_url TEXT,
  department TEXT,
  last_scanned_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================
-- SKILL REGISTRY TABLE
-- ============================================
CREATE TABLE skill_registry (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  skill_id TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  department TEXT,
  category TEXT,
  source_id UUID REFERENCES skill_sources(id) ON DELETE CASCADE,
  author_name TEXT,
  license TEXT,
  original_path TEXT,
  current_version TEXT DEFAULT '1.0.0',
  versions JSONB DEFAULT '[]'::jsonb,
  content_hash TEXT,
  is_expert_skill BOOLEAN DEFAULT false,
  is_core_skill BOOLEAN DEFAULT false,
  has_command BOOLEAN DEFAULT false,
  keywords TEXT[] DEFAULT '{}',
  discovered_at TIMESTAMPTZ,
  last_checked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_skill_registry_source ON skill_registry(source_id);
CREATE INDEX idx_skill_registry_dept ON skill_registry(department);
CREATE INDEX idx_skill_registry_type ON skill_registry(is_expert_skill, is_core_skill);
CREATE INDEX idx_skill_registry_keywords ON skill_registry USING GIN(keywords);

-- ============================================
-- SKILL MATCHES TABLE
-- ============================================
CREATE TABLE skill_matches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  expert_skill_id UUID REFERENCES skill_registry(id) ON DELETE CASCADE,
  core_skill_slug TEXT NOT NULL,
  match_type TEXT,
  confidence NUMERIC(5,4) DEFAULT 0,
  reasoning TEXT,
  review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected', 'override')),
  reviewer_notes TEXT,
  reviewed_at TIMESTAMPTZ,
  reviewed_by TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_skill_matches_expert ON skill_matches(expert_skill_id);
CREATE INDEX idx_skill_matches_status ON skill_matches(review_status);
CREATE UNIQUE INDEX idx_skill_matches_pair ON skill_matches(expert_skill_id, core_skill_slug);

-- ============================================
-- SKILL ADOPTIONS TABLE
-- ============================================
CREATE TABLE skill_adoptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  expert_skill_id UUID REFERENCES skill_registry(id) ON DELETE CASCADE,
  adopted_at TIMESTAMPTZ DEFAULT now(),
  adopted_version TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_skill_adoptions_expert ON skill_adoptions(expert_skill_id);

-- ============================================
-- TRIGGERS
-- ============================================
CREATE TRIGGER skill_sources_updated_at
  BEFORE UPDATE ON skill_sources
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER skill_registry_updated_at
  BEFORE UPDATE ON skill_registry
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER skill_matches_updated_at
  BEFORE UPDATE ON skill_matches
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================
ALTER TABLE skill_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_adoptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read skill_sources" ON skill_sources FOR SELECT USING (true);
CREATE POLICY "Public read skill_registry" ON skill_registry FOR SELECT USING (true);
CREATE POLICY "Public read skill_matches" ON skill_matches FOR SELECT USING (true);
CREATE POLICY "Public read skill_adoptions" ON skill_adoptions FOR SELECT USING (true);

CREATE POLICY "Service full access skill_sources" ON skill_sources FOR ALL USING (true);
CREATE POLICY "Service full access skill_registry" ON skill_registry FOR ALL USING (true);
CREATE POLICY "Service full access skill_matches" ON skill_matches FOR ALL USING (true);
CREATE POLICY "Service full access skill_adoptions" ON skill_adoptions FOR ALL USING (true);

-- ============================================
-- VIEWS
-- ============================================
CREATE VIEW skill_stats AS
SELECT
  COUNT(*) as total_skills,
  COUNT(*) FILTER (WHERE is_core_skill) as core_skills,
  COUNT(*) FILTER (WHERE is_expert_skill) as expert_skills,
  COUNT(*) FILTER (WHERE has_command) as command_skills,
  COUNT(DISTINCT department) as departments
FROM skill_registry;

CREATE VIEW skill_match_stats AS
SELECT
  COUNT(*) as total_matches,
  COUNT(*) FILTER (WHERE review_status = 'pending') as pending_reviews,
  COUNT(*) FILTER (WHERE review_status = 'approved') as approved,
  COUNT(*) FILTER (WHERE review_status = 'rejected') as rejected,
  COUNT(*) FILTER (WHERE review_status = 'override') as overrides
FROM skill_matches;
