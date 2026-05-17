# Architecture

AI.JBHerrera is a multi-tool web app: a static frontend in `public/` and Python serverless functions in `api/`, all deployed on Vercel.

## Layout

```
ai-tools/
├── public/          Static frontend (HTML/CSS/JS, no build step)
│   ├── styles/
│   │   └── base.css     Shared design system tokens & components
│   ├── _template/
│   │   └── page.html    Starter scaffold for new pages
│   └── *.html           One file per page (digest, ai-stack, skills, …)
├── api/             Vercel Python serverless functions
│   ├── shared.py        Core enrichment pipeline + RSS feed list
│   ├── lib/supabase.py  DB client (used when USE_DATABASE=true)
│   ├── admin/           Token-gated admin endpoints
│   └── *.py             One file per endpoint
├── db/              Supabase schema + seed SQL
├── docs/            This folder
├── archive/         Retired files (not part of the build)
└── vercel.json      Routing + function config
```

## API layer (`api/`)

Each `.py` file is a Vercel function using Python's `BaseHTTPRequestHandler` (not Flask/FastAPI — Vercel's Python runtime expects this).

- **Public endpoints** (no auth): `feeds.py`, `fetch-feed.py`, `export.py`, `summarize.py`, `skills.py`
- **Admin endpoints** (require `ADMIN_API_TOKEN` header, skipped in dev): `admin/feeds.py`, `admin/icps.py`, `admin/categories.py`, `admin/discover.py`, `admin/skills.py`
- **Shared logic** (`shared.py`): Hardcoded RSS feed list, article enrichment pipeline, scoring functions. The most important backend file.
- **Database client** (`lib/supabase.py`): All Supabase reads/writes. Used only when `USE_DATABASE=true`.

Routing from URL → handler is declared in `vercel.json`.

## Article enrichment pipeline (`api/shared.py`)

When a feed is fetched, each article runs through `enrich_article()`:

1. `is_ai_relevant()` — keyword-based AI relevance filter
2. `calculate_smb_score()` — small-business relevance (0–10)
3. `categorize_article()` — one of 7 categories (Big Tech, Funding, Product News, Research, Policy, SMB Focus, General)
4. `calculate_viral_score()` — trending potential (0–10)
5. `generate_impact()` — general + SMB-specific impact statements
6. `generate_viral_suggestions()` — content ideas
7. `extract_key_bullets()` — 2–3 key points from summary
8. ICP pain-point matching — maps articles to predefined business pain signals

## Data layer

Two modes, switched by `USE_DATABASE`:

- **Database mode** (`USE_DATABASE=true`): Supabase Postgres. Schema in `db/schema.sql`, seed in `db/seed_feeds.sql`. Tables: `feeds`, `categories`, `icp_profiles`, `feed_suggestions`, `digest_history`.
- **Dev/fallback mode** (default): Hardcoded `RSS_FEEDS` dict in `api/shared.py`.

ICP profiles use JSONB storage with structured fields: `audience_overview`, `pain_points`, `language_patterns`, `desired_transformation`.

## Summarization (`api/summarize.py`)

Uses Anthropic Claude API to summarize articles. Fetches full content via BeautifulSoup, sends to Claude with structured prompts. 60-second Vercel timeout — configured in `vercel.json`.

## Frontend

Vanilla HTML/JS, no build step. Every page loads `/styles/base.css` first, then page-specific styles inline. The design system is documented in `design-standard.md`. The standard for adding a new page is in `add-new-page.md`.

## Conventions

- All dates are UTC-aware `datetime` objects.
- Admin endpoints check `ADMIN_API_TOKEN` but skip auth in dev (token unset).
- Sensitive config lives in `.env` (gitignored). `.env.example` lists required keys.
- Folders are kebab-case lowercase.
