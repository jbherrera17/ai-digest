-- AIDigest Database Schema
-- Run this in Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- CATEGORIES TABLE
-- ============================================
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,
  display_order INTEGER DEFAULT 0,
  color TEXT DEFAULT '#6366f1', -- Tailwind indigo-500
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Insert default categories
INSERT INTO categories (name, display_order, color) VALUES
  ('Tech News', 1, '#3b82f6'),
  ('AI News', 2, '#8b5cf6'),
  ('Company Blog', 3, '#10b981'),
  ('Newsletter', 4, '#f59e0b'),
  ('Substack', 5, '#ec4899'),
  ('Medium', 6, '#06b6d4'),
  ('Research & Policy', 7, '#6366f1'),
  ('Enterprise AI', 8, '#14b8a6');

-- ============================================
-- FEEDS TABLE
-- ============================================
CREATE TABLE feeds (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  priority INTEGER DEFAULT 2 CHECK (priority IN (1, 2, 3)),
  feed_type TEXT DEFAULT 'news' CHECK (feed_type IN ('news', 'newsletter', 'blog', 'substack', 'medium')),
  is_active BOOLEAN DEFAULT true,
  description TEXT,
  last_fetched_at TIMESTAMPTZ,
  fetch_error TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index for active feeds lookup
CREATE INDEX idx_feeds_active ON feeds(is_active) WHERE is_active = true;
CREATE INDEX idx_feeds_category ON feeds(category);

-- ============================================
-- ICP PROFILES TABLE
-- ============================================
CREATE TABLE icp_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  -- Structured data from JSON or parsed from text
  data JSONB NOT NULL,
  -- Quick access fields extracted from data
  pain_points TEXT[] DEFAULT '{}',
  keywords TEXT[] DEFAULT '{}',
  -- Source tracking
  source_type TEXT DEFAULT 'json' CHECK (source_type IN ('json', 'text', 'insight360')),
  insight360_id UUID, -- Reference to Insight360 ICP if applicable
  -- Status
  is_active BOOLEAN DEFAULT true,
  is_default BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Only one default ICP at a time
CREATE UNIQUE INDEX idx_icp_default ON icp_profiles(is_default) WHERE is_default = true;

-- ============================================
-- FEED DISCOVERY - Curated suggestions
-- ============================================
CREATE TABLE feed_suggestions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  description TEXT,
  category TEXT NOT NULL,
  feed_type TEXT DEFAULT 'news',
  relevance_tags TEXT[] DEFAULT '{}', -- e.g., ['ai', 'business', 'marketing']
  popularity_score INTEGER DEFAULT 50 CHECK (popularity_score BETWEEN 0 AND 100),
  is_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for tag-based discovery
CREATE INDEX idx_feed_suggestions_tags ON feed_suggestions USING GIN(relevance_tags);

-- ============================================
-- DIGEST HISTORY (for future use)
-- ============================================
CREATE TABLE digest_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  generated_at TIMESTAMPTZ DEFAULT now(),
  icp_profile_id UUID REFERENCES icp_profiles(id),
  feeds_used UUID[] DEFAULT '{}',
  article_count INTEGER DEFAULT 0,
  top_stories JSONB DEFAULT '[]',
  config JSONB DEFAULT '{}', -- Store generation params (days, filters, etc.)
  markdown_export TEXT
);

-- ============================================
-- ADMIN SETTINGS
-- ============================================
CREATE TABLE admin_settings (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Default settings
INSERT INTO admin_settings (key, value) VALUES
  ('default_days', '3'),
  ('max_articles_per_feed', '20'),
  ('ai_keywords', '["AI", "artificial intelligence", "machine learning", "ML", "GPT", "LLM", "large language model", "neural network", "deep learning", "ChatGPT", "Claude", "Gemini", "OpenAI", "Anthropic", "generative AI", "gen AI", "automation", "natural language", "NLP", "computer vision", "robotics", "AGI", "transformer"]'),
  ('smb_keywords', '["small business", "SMB", "SME", "entrepreneur", "startup", "founder", "solopreneur", "freelance", "bootstrap", "indie"]'),
  ('viral_keywords', '["breaking", "exclusive", "leaked", "major", "massive", "revolutionary", "game-changing", "disrupting", "shocking", "unprecedented", "first-ever", "billion", "million", "raises", "acquires", "launches", "announces", "releases", "unveils", "introduces", "breakthrough", "surpasses"]');

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE feeds ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE icp_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE feed_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE digest_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_settings ENABLE ROW LEVEL SECURITY;

-- Public read access for feeds (needed for digest generation)
CREATE POLICY "Public read access for active feeds" ON feeds
  FOR SELECT USING (is_active = true);

-- Public read access for categories
CREATE POLICY "Public read access for categories" ON categories
  FOR SELECT USING (true);

-- Public read access for active ICP profiles
CREATE POLICY "Public read access for active ICPs" ON icp_profiles
  FOR SELECT USING (is_active = true);

-- Public read access for feed suggestions
CREATE POLICY "Public read access for feed suggestions" ON feed_suggestions
  FOR SELECT USING (true);

-- Admin full access (authenticated users)
CREATE POLICY "Admin full access to feeds" ON feeds
  FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Admin full access to categories" ON categories
  FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Admin full access to ICP profiles" ON icp_profiles
  FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Admin full access to feed suggestions" ON feed_suggestions
  FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Admin full access to digest history" ON digest_history
  FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Admin full access to settings" ON admin_settings
  FOR ALL USING (auth.role() = 'authenticated');

-- ============================================
-- FUNCTIONS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables
CREATE TRIGGER feeds_updated_at
  BEFORE UPDATE ON feeds
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER categories_updated_at
  BEFORE UPDATE ON categories
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER icp_profiles_updated_at
  BEFORE UPDATE ON icp_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Function to extract pain points and keywords from ICP data
CREATE OR REPLACE FUNCTION extract_icp_fields()
RETURNS TRIGGER AS $$
BEGIN
  -- Extract pain points from data.pain_points.top_pains
  IF NEW.data ? 'pain_points' AND NEW.data->'pain_points' ? 'top_pains' THEN
    NEW.pain_points = ARRAY(SELECT jsonb_array_elements_text(NEW.data->'pain_points'->'top_pains'));
  END IF;

  -- Extract keywords from data.language_patterns.keywords_used
  IF NEW.data ? 'language_patterns' AND NEW.data->'language_patterns' ? 'keywords_used' THEN
    NEW.keywords = ARRAY(SELECT jsonb_array_elements_text(NEW.data->'language_patterns'->'keywords_used'));
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER icp_extract_fields
  BEFORE INSERT OR UPDATE ON icp_profiles
  FOR EACH ROW EXECUTE FUNCTION extract_icp_fields();

-- ============================================
-- VIEWS
-- ============================================

-- Active feeds with category info
CREATE VIEW active_feeds_view AS
SELECT
  f.id,
  f.name,
  f.url,
  f.category,
  f.priority,
  f.feed_type,
  f.description,
  f.last_fetched_at,
  c.color as category_color,
  c.display_order as category_order
FROM feeds f
LEFT JOIN categories c ON f.category = c.name
WHERE f.is_active = true
ORDER BY c.display_order, f.priority, f.name;

-- Feed stats
CREATE VIEW feed_stats AS
SELECT
  category,
  COUNT(*) as total_feeds,
  COUNT(*) FILTER (WHERE is_active) as active_feeds,
  COUNT(*) FILTER (WHERE feed_type = 'news') as news_count,
  COUNT(*) FILTER (WHERE feed_type = 'newsletter') as newsletter_count,
  COUNT(*) FILTER (WHERE feed_type = 'blog') as blog_count,
  COUNT(*) FILTER (WHERE feed_type = 'substack') as substack_count,
  COUNT(*) FILTER (WHERE feed_type = 'medium') as medium_count
FROM feeds
GROUP BY category
ORDER BY category;
