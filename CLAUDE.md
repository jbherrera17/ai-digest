# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Digest — a web app that aggregates AI news from 50+ RSS feeds, enriches articles with relevance scoring and business impact analysis, and generates formatted digests. Deployed on Vercel as Python serverless functions with a vanilla JS frontend.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (serves frontend + API)
vercel dev
# Main UI: http://localhost:3000
# Admin panel: http://localhost:3000/admin

# Deploy to production
vercel --prod

# Standalone digest generation (legacy script, separate from web app)
python ai_digest_generator.py --days 7
```

## Architecture

**Serverless Python API + static frontend, dual-mode data layer (Supabase or hardcoded fallback).**

### API Layer (`api/`)

Each `.py` file in `api/` is a Vercel serverless function using `BaseHTTPRequestHandler`. Routing is defined in `vercel.json`.

- **Public endpoints** (no auth): `feeds.py`, `fetch-feed.py`, `export.py`, `summarize.py`
- **Admin endpoints** (require `ADMIN_API_TOKEN` header): `admin/feeds.py`, `admin/icps.py`, `admin/categories.py`, `admin/discover.py`
- **Shared logic** (`shared.py`): Core module containing the hardcoded feed list, article enrichment pipeline, and all scoring functions. This is the most important backend file.
- **Database client** (`lib/supabase.py`): All Supabase operations. Used when `USE_DATABASE=true`.

### Article Enrichment Pipeline (`api/shared.py`)

When a feed is fetched, each article passes through this pipeline in `enrich_article()`:
1. `is_ai_relevant()` — keyword-based AI relevance filter
2. `calculate_smb_score()` — rates relevance to small businesses (0-10)
3. `categorize_article()` — assigns one of 7 categories (Big Tech, Funding, Product News, Research, Policy, SMB Focus, General)
4. `calculate_viral_score()` — trending potential (0-10)
5. `generate_impact()` — general + SMB-specific business impact statements
6. `generate_viral_suggestions()` — content creation ideas
7. `extract_key_bullets()` — 2-3 key points from summary
8. ICP pain point matching — maps articles to predefined business pain signals

### Frontend (`public/`)

Vanilla HTML/JS (no build step). Three pages:
- `index.html` — Main digest viewer, fetches and displays enriched articles
- `admin.html` — Feed/ICP/category management panel (~1500 lines, largest file)
- `digest.html` — Export-focused digest view

### Data Layer

Two modes controlled by `USE_DATABASE` env var:
- **Database mode**: Supabase PostgreSQL (schema in `db/schema.sql`, seed data in `db/seed_feeds.sql`)
- **Dev/fallback mode**: Hardcoded `RSS_FEEDS` dict in `api/shared.py`

Tables: `feeds`, `categories`, `icp_profiles`, `feed_suggestions`, `digest_history`

### Summarization (`api/summarize.py`)

Uses Anthropic Claude API to generate article summaries. Fetches full article content via BeautifulSoup, sends to Claude with structured prompts. Has 60-second Vercel function timeout configured in `vercel.json`.

## Environment Variables

See `.env.example`. Key vars: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `USE_DATABASE`, `ADMIN_API_TOKEN`, `ANTHROPIC_API_KEY`.

## Conventions

- API handlers use Python's `BaseHTTPRequestHandler` (not Flask/FastAPI) for Vercel compatibility
- Admin endpoints check `ADMIN_API_TOKEN` but skip auth in dev mode (no token set)
- ICP profiles use JSONB storage with structured fields (audience_overview, pain_points, language_patterns, desired_transformation)
- All dates should be UTC-aware datetimes
