# AIDigest Setup Guide

This guide walks you through setting up AIDigest with the new database-driven configuration system.

## Quick Start (Development Mode)

For local development without a database:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run locally:**
   ```bash
   vercel dev
   ```

3. **Access the app:**
   - Main digest: http://localhost:3000
   - Admin panel: http://localhost:3000/admin

In development mode (without `USE_DATABASE=true`), the app uses the hardcoded feeds from `api/shared.py`.

---

## Production Setup with Supabase

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your project URL and API keys from Settings > API

### Step 2: Set Up Database Schema

1. Go to the SQL Editor in your Supabase dashboard
2. Run the schema file: `db/schema.sql`
3. Run the seed file: `db/seed_feeds.sql`

This creates:
- `feeds` table - RSS feed configurations
- `categories` table - Feed groupings
- `icp_profiles` table - ICP profile storage
- `feed_suggestions` table - Discovery recommendations
- `admin_settings` table - App configuration
- `digest_history` table - For future digest tracking

### Step 3: Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Public anon key (for read operations) |
| `SUPABASE_SERVICE_KEY` | Service role key (for admin operations) |
| `USE_DATABASE` | Set to `true` to enable database mode |
| `ADMIN_API_TOKEN` | Optional security token for admin API |

### Step 4: Deploy to Vercel

1. **Connect your repository to Vercel**

2. **Add environment variables in Vercel dashboard:**
   - Go to Settings > Environment Variables
   - Add all variables from your `.env` file

3. **Deploy:**
   ```bash
   vercel --prod
   ```

---

## Admin Panel Usage

Access the admin panel at `/admin` on your deployed site.

### Authentication

- **Dev mode:** Leave token blank and click Sign In
- **Production:** Set `ADMIN_API_TOKEN` and enter it to authenticate

### Managing Feeds

1. **Add Feed:**
   - Click "Add Feed"
   - Enter name and RSS URL
   - Click "Validate URL" to verify it works
   - Select category, type, and priority
   - Save

2. **Edit Feed:**
   - Click "Edit" on any feed row
   - Make changes and save

3. **Toggle Active:**
   - Use the toggle switch to enable/disable feeds

4. **Discover Feeds:**
   - Go to Discover section
   - Select your industry niche
   - Browse recommendations
   - Select feeds to add
   - Click "Add Selected"

### Managing ICP Profiles

1. **Add from Text:**
   - Click "Add Profile"
   - Select "Paste Text" tab
   - Describe your ICP in plain English
   - Click "Parse & Preview"
   - Review extracted data
   - Save

2. **Add from JSON:**
   - Select "Upload JSON" tab
   - Upload or paste ICP JSON file
   - Save

3. **Set Default:**
   - Check "Set as Default" when saving
   - The default ICP is used for digest impact analysis

### ICP JSON Format

```json
{
  "audience_overview": {
    "one_sentence_summary": "...",
    "primary_identity": "Small business coaches"
  },
  "pain_points": {
    "top_pains": [
      "Content marketing treadmill",
      "Scaling beyond 1:1 sessions"
    ]
  },
  "language_patterns": {
    "keywords_used": ["automation", "passive income", "courses"]
  },
  "desired_transformation": {
    "outcomes": ["Build passive income", "Scale their practice"]
  }
}
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                            │
├─────────────────────────────────────────────────────────┤
│  /public/index.html    │  /public/admin.html            │
│  Main Digest UI        │  Admin Configuration Panel     │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                    API Endpoints                         │
├─────────────────────────────────────────────────────────┤
│  /api/feeds          - List feeds (DB or hardcoded)     │
│  /api/fetch-feed     - Fetch & enrich articles          │
│  /api/export         - Export digest as markdown        │
│  /api/admin/feeds    - Feed CRUD (admin)                │
│  /api/admin/icps     - ICP profile CRUD (admin)         │
│  /api/admin/discover - Feed discovery (admin)           │
│  /api/admin/categories - Category CRUD (admin)          │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
├─────────────────────────────────────────────────────────┤
│  Supabase PostgreSQL  │  Hardcoded Fallback            │
│  (when USE_DATABASE   │  (api/shared.py RSS_FEEDS)     │
│   = true)             │                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Migrating Existing Feeds

The `db/seed_feeds.sql` file contains INSERT statements for all 50+ feeds from the original `api/shared.py`. Run this in Supabase SQL Editor after creating the schema.

To add custom feeds not in the seed file:
1. Use the Admin Panel (recommended)
2. Or add INSERT statements to the seed file

---

## Insight360 Integration

AIDigest is designed to work as a module within Insight360:

1. **Shared Supabase:** Use the same Supabase project
2. **ICP Import:** Pull ICPs from Insight360's `icp_profiles` table
3. **Unified Auth:** Share Supabase Auth for user management

Set `source_type = 'insight360'` and `insight360_id` when importing ICPs from Insight360.

---

## Troubleshooting

### "Database error, falling back to hardcoded feeds"
- Check that `SUPABASE_URL` and keys are set correctly
- Verify `USE_DATABASE=true` is set
- Check Supabase dashboard for RLS policy issues

### Admin API returns 401
- Set `ADMIN_API_TOKEN` in environment
- Enter the token in the admin login screen

### Feeds not loading
- Check browser console for errors
- Verify CORS headers in API responses
- Test the `/api/feeds` endpoint directly

### ICP parsing not working
- Provide more descriptive text with pain points and keywords
- Check the preview before saving
- Try the JSON upload method as fallback

---

## Files Reference

| File | Purpose |
|------|---------|
| `db/schema.sql` | Database schema |
| `db/seed_feeds.sql` | Initial feed data |
| `api/lib/supabase.py` | Supabase client |
| `api/admin/*.py` | Admin API endpoints |
| `api/shared.py` | Feed config & enrichment |
| `public/admin.html` | Admin panel UI |
| `public/index.html` | Main digest UI |
| `vercel.json` | Routing config |
