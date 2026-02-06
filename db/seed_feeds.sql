-- AIDigest Feed Migration
-- Migrates existing 50+ RSS feeds from hardcoded config to database
-- Run this after schema.sql

-- ============================================
-- ADDITIONAL CATEGORIES (from existing feeds)
-- ============================================
INSERT INTO categories (name, display_order, color) VALUES
  ('Deep Tech', 9, '#7c3aed'),
  ('Tech Culture', 10, '#db2777'),
  ('Consumer Tech', 11, '#0891b2'),
  ('Business Tech', 12, '#059669'),
  ('AI Platform', 13, '#d97706'),
  ('AI Infrastructure', 14, '#dc2626'),
  ('Productivity AI', 15, '#4f46e5'),
  ('Cloud AI', 16, '#0284c7'),
  ('Company News', 17, '#16a34a')
ON CONFLICT (name) DO UPDATE SET display_order = EXCLUDED.display_order, color = EXCLUDED.color;

-- ============================================
-- TECH NEWS SOURCES
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('TechCrunch AI', 'https://techcrunch.com/category/artificial-intelligence/feed/', 'Tech News', 1, 'news'),
  ('SiliconANGLE AI', 'https://siliconangle.com/category/ai/feed/', 'Business Tech', 1, 'news'),
  ('MIT Technology Review', 'https://www.technologyreview.com/feed/', 'Research & Policy', 2, 'news'),
  ('Ars Technica AI', 'https://arstechnica.com/tag/artificial-intelligence/feed/', 'Deep Tech', 2, 'news'),
  ('Wired AI', 'https://www.wired.com/feed/tag/ai/latest/rss', 'Tech Culture', 2, 'news'),
  ('The Verge AI', 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml', 'Consumer Tech', 2, 'news'),
  ('AI Business', 'https://aibusiness.com/rss.xml', 'Enterprise AI', 1, 'news'),
  ('Artificial Intelligence News', 'https://www.artificialintelligence-news.com/feed/', 'AI News', 2, 'news'),
  ('VentureBeat AI', 'https://venturebeat.com/category/ai/feed/', 'Enterprise AI', 1, 'news')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- COMPANY NEWS / BLOGS - AI Labs
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('OpenAI Blog', 'https://openai.com/blog/rss.xml', 'Company News', 1, 'blog'),
  ('Google AI Blog', 'https://blog.google/technology/ai/rss/', 'Company News', 1, 'blog'),
  ('Anthropic Blog', 'https://www.anthropic.com/research/rss.xml', 'Company Blog', 1, 'blog'),
  ('Meta AI Blog', 'https://ai.meta.com/blog/rss/', 'Company Blog', 1, 'blog'),
  ('Microsoft AI Blog', 'https://blogs.microsoft.com/ai/feed/', 'Company Blog', 1, 'blog'),
  ('Amazon AI Blog', 'https://aws.amazon.com/blogs/machine-learning/feed/', 'Company Blog', 2, 'blog'),
  ('Apple Machine Learning', 'https://machinelearning.apple.com/rss.xml', 'Company Blog', 2, 'blog')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- COMPANY BLOGS - AI Infrastructure
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('NVIDIA Blog', 'https://blogs.nvidia.com/feed/', 'AI Infrastructure', 1, 'blog'),
  ('AMD AI Blog', 'https://community.amd.com/t5/ai/bg-p/amd-ai/label-name/blog', 'AI Infrastructure', 2, 'blog')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- COMPANY BLOGS - AI Platforms
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('Hugging Face Blog', 'https://huggingface.co/blog/feed.xml', 'AI Platform', 1, 'blog'),
  ('Stability AI Blog', 'https://stability.ai/blog/rss.xml', 'AI Platform', 2, 'blog'),
  ('Cohere Blog', 'https://cohere.com/blog/rss.xml', 'AI Platform', 2, 'blog'),
  ('Mistral AI Blog', 'https://mistral.ai/feed.xml', 'AI Platform', 2, 'blog'),
  ('Perplexity Blog', 'https://www.perplexity.ai/hub/blog/rss.xml', 'AI Platform', 2, 'blog')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- COMPANY BLOGS - Enterprise / Productivity
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('Salesforce AI Blog', 'https://blog.salesforceairesearch.com/rss/', 'Enterprise AI', 2, 'blog'),
  ('Notion AI Blog', 'https://www.notion.so/blog/rss.xml', 'Productivity AI', 2, 'blog'),
  ('Canva AI Blog', 'https://www.canva.dev/blog/engineering/feed.xml', 'Productivity AI', 2, 'blog')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- COMPANY BLOGS - Cloud Platforms
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('Google Cloud AI Blog', 'https://cloud.google.com/blog/products/ai-machine-learning/rss', 'Cloud AI', 2, 'blog'),
  ('AWS Machine Learning Blog', 'https://aws.amazon.com/blogs/aws/category/artificial-intelligence/feed/', 'Cloud AI', 2, 'blog')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- NEWSLETTERS
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('The AI Newsletter (Towards AI)', 'https://pub.towardsai.net/feed', 'Newsletter', 2, 'newsletter'),
  ('Import AI Newsletter', 'https://importai.substack.com/feed', 'Newsletter', 2, 'newsletter'),
  ('The Batch (deeplearning.ai)', 'https://www.deeplearning.ai/the-batch/feed/', 'Newsletter', 1, 'newsletter'),
  ('TLDR AI', 'https://tldr.tech/ai/rss', 'Newsletter', 1, 'newsletter'),
  ('Ben''s Bites', 'https://bensbites.beehiiv.com/feed', 'Newsletter', 2, 'newsletter'),
  ('The Neuron', 'https://www.theneurondaily.com/feed', 'Newsletter', 2, 'newsletter')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- SUBSTACK SUBSCRIPTIONS
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('Nate''s Newsletter', 'https://natesnewsletter.substack.com/feed', 'Substack', 2, 'substack'),
  ('Sergei AI', 'https://sergeiai.substack.com/feed', 'Substack', 2, 'substack'),
  ('The Algorithmic Bridge', 'https://www.thealgorithmicbridge.com/feed', 'Substack', 2, 'substack'),
  ('ByteByteGo', 'https://blog.bytebytego.com/feed', 'Substack', 2, 'substack'),
  ('Concept Bureau', 'https://conceptbureau.substack.com/feed', 'Substack', 2, 'substack'),
  ('AI Search', 'https://aisearch.substack.com/feed', 'Substack', 2, 'substack'),
  ('AI Supremacy', 'https://www.ai-supremacy.com/feed', 'Substack', 2, 'substack'),
  ('Latent Space', 'https://www.latent.space/feed', 'Substack', 1, 'substack'),
  ('Excellent Prompts', 'https://excellentprompts.substack.com/feed', 'Substack', 2, 'substack')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- MEDIUM FOLLOWS
-- ============================================
INSERT INTO feeds (name, url, category, priority, feed_type) VALUES
  ('Towards AI (Medium)', 'https://medium.com/feed/towards-artificial-intelligence', 'Medium', 2, 'medium'),
  ('UX Collective (Medium)', 'https://medium.com/feed/ux-collective', 'Medium', 2, 'medium'),
  ('Gaurav Jain (Medium)', 'https://medium.com/feed/@gauravjain', 'Medium', 2, 'medium'),
  ('AI Advances (Medium)', 'https://medium.com/feed/ai-advances', 'Medium', 2, 'medium'),
  ('Generative AI (Medium)', 'https://medium.com/feed/generative-ai', 'Medium', 2, 'medium'),
  ('UX Planet (Medium)', 'https://medium.com/feed/ux-planet', 'Medium', 2, 'medium'),
  ('Entrepreneurship Handbook (Medium)', 'https://medium.com/feed/entrepreneurs-handbook', 'Medium', 2, 'medium'),
  ('AI in Plain English (Medium)', 'https://medium.com/feed/ai-in-plain-english', 'Medium', 2, 'medium'),
  ('Alberto Romero (Medium)', 'https://medium.com/feed/@albertoromgar', 'Medium', 2, 'medium')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, priority = EXCLUDED.priority;

-- ============================================
-- FEED DISCOVERY SUGGESTIONS
-- Pre-populated curated list for feed discovery feature
-- ============================================
INSERT INTO feed_suggestions (name, url, description, category, feed_type, relevance_tags, popularity_score, is_verified) VALUES
  -- AI/Tech focused
  ('Hacker News', 'https://hnrss.org/frontpage', 'Top stories from Hacker News community', 'Tech News', 'news', ARRAY['tech', 'startups', 'ai', 'programming'], 95, true),
  ('Product Hunt', 'https://www.producthunt.com/feed', 'New tech products and tools daily', 'Tech News', 'news', ARRAY['products', 'startups', 'tools'], 90, true),
  ('a]6z', 'https://a16z.com/feed/', 'Andreessen Horowitz tech insights', 'Newsletter', 'blog', ARRAY['vc', 'startups', 'ai', 'business'], 85, true),
  ('First Round Review', 'https://review.firstround.com/feed.xml', 'Startup advice and operator insights', 'Newsletter', 'blog', ARRAY['startups', 'management', 'growth'], 88, true),
  ('Stratechery', 'https://stratechery.com/feed/', 'Tech strategy analysis by Ben Thompson', 'Newsletter', 'newsletter', ARRAY['strategy', 'tech', 'business'], 92, true),
  ('Lenny''s Newsletter', 'https://www.lennysnewsletter.com/feed', 'Product, growth, and career advice', 'Substack', 'substack', ARRAY['product', 'growth', 'career'], 90, true),

  -- Business/Marketing
  ('Seth Godin', 'https://seths.blog/feed/', 'Marketing and business wisdom', 'Newsletter', 'blog', ARRAY['marketing', 'business', 'leadership'], 85, true),
  ('Marketing Examples', 'https://marketingexamples.com/feed.xml', 'Real-world marketing case studies', 'Newsletter', 'blog', ARRAY['marketing', 'copywriting', 'growth'], 80, true),
  ('Indie Hackers', 'https://www.indiehackers.com/feed.xml', 'Stories from bootstrapped founders', 'Newsletter', 'blog', ARRAY['startups', 'bootstrap', 'business'], 82, true),
  ('The Bootstrapped Founder', 'https://thebootstrappedfounder.com/feed/', 'Building businesses without VC', 'Substack', 'substack', ARRAY['bootstrap', 'saas', 'business'], 78, true),

  -- Industry specific
  ('Healthcare IT News', 'https://www.healthcareitnews.com/feed', 'Healthcare technology news', 'Tech News', 'news', ARRAY['healthcare', 'healthtech', 'ai'], 75, true),
  ('IndustryWeek', 'https://www.industryweek.com/rss.xml', 'Manufacturing and operations news', 'Tech News', 'news', ARRAY['manufacturing', 'operations', 'industry'], 70, true),
  ('Above the Law', 'https://abovethelaw.com/feed/', 'Legal industry news and tech', 'Tech News', 'news', ARRAY['legal', 'law', 'legaltech'], 72, true),
  ('Accounting Today', 'https://www.accountingtoday.com/feed', 'Accounting and finance tech', 'Tech News', 'news', ARRAY['accounting', 'finance', 'tax'], 68, true),

  -- Developer/Technical
  ('Dev.to', 'https://dev.to/feed', 'Developer community articles', 'Tech News', 'blog', ARRAY['programming', 'ai', 'web'], 85, true),
  ('The Pragmatic Engineer', 'https://newsletter.pragmaticengineer.com/feed', 'Engineering leadership and big tech insights', 'Substack', 'substack', ARRAY['engineering', 'career', 'tech'], 88, true),
  ('Simon Willison', 'https://simonwillison.net/atom/everything/', 'AI and development insights', 'Newsletter', 'blog', ARRAY['ai', 'llm', 'programming'], 82, true),
  ('Chip Huyen', 'https://huyenchip.com/feed.xml', 'ML systems and AI engineering', 'Newsletter', 'blog', ARRAY['ml', 'ai', 'engineering'], 80, true)
ON CONFLICT (url) DO NOTHING;
