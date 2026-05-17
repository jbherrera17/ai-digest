# Deployment

Deployed on Vercel as Python serverless functions + static frontend.

## Commands

```bash
# Install Python deps
pip install -r requirements.txt

# Run locally (frontend + API on http://localhost:3000)
vercel dev

# Preview deploy (per-branch URL)
vercel

# Production deploy
vercel --prod
```

## Environment variables

Defined in `.env` (gitignored). Template in `.env.example`. Required keys:

| Variable | Purpose |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Public anon key (frontend reads) |
| `SUPABASE_SERVICE_KEY` | Service-role key (admin writes) |
| `USE_DATABASE` | `true` to use Supabase, unset for hardcoded fallback |
| `ADMIN_API_TOKEN` | Bearer token gating `api/admin/*` endpoints (skipped in dev) |
| `ANTHROPIC_API_KEY` | Claude API for `api/summarize.py` |

To sync local `.env` from Vercel:

```bash
vercel env pull
```

To add a new variable:

```bash
vercel env add <NAME>
```

## Function configuration

In `vercel.json`:

- `api/summarize.py` has a 60-second `maxDuration` (Claude calls can be slow).
- All other functions use the platform default (300s on current Vercel).

## Pre-flight before pushing

Per the project engineering checklist:

1. Pages load — visually confirm content renders, not just HTTP 200.
2. Links navigate — click every affected link.
3. Images render — confirm visible display.
4. Interactive elements work — buttons aren't hidden behind the fixed navbar.

## After deploying

1. Wait for the Vercel deployment to finish.
2. Test the live URL (not just local).
3. Walk one full user flow end-to-end (e.g. index → digest → article → back).
