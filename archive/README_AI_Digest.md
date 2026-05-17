# AI News Digest Automation Package

## Overview

This package allows you to automatically pull AI news from multiple RSS sources and generate a formatted weekly digest for your newsletter.

## Files Included

| File | Description |
|------|-------------|
| `ai_digest_generator.py` | Main Python script that fetches RSS feeds and generates digest |
| `AI_RSS_Feed_List.docx` | Reference document with all RSS sources |
| `AI_Newsletter_Template.docx` | Ready-to-use newsletter template |

## Quick Start

### 1. Install Dependencies

```bash
pip install feedparser requests python-dateutil
```

### 2. Run the Script

```bash
# Generate digest for past 7 days (default)
python ai_digest_generator.py

# Generate digest for past 3 days
python ai_digest_generator.py --days 3

# Save output to a file
python ai_digest_generator.py --output weekly_digest.md

# Combine options
python ai_digest_generator.py --days 7 --output my_digest.md
```

### 3. Use the Output

The script generates a structured digest with:
- **Top Stories** - The 5 most important AI articles
- **SMB AI Spotlight** - Articles most relevant to small/mid-sized businesses
- **Quick Hits by Topic** - Organized by category (Big Tech, Funding, Product News, Research, Policy, SMB Focus)

Copy the relevant sections into your `AI_Newsletter_Template.docx` to create your newsletter.

## RSS Sources Included

### Primary News Sources
- TechCrunch AI
- VentureBeat AI
- SiliconANGLE AI
- MIT Technology Review
- Ars Technica AI
- Wired AI
- The Verge AI

### AI-Specific Sources
- AI Business
- Artificial Intelligence News

### Company Blogs
- OpenAI Blog
- Google AI Blog

## Customizing the Script

### Add New RSS Feeds

Edit the `RSS_FEEDS` dictionary in `ai_digest_generator.py`:

```python
RSS_FEEDS = {
    "Your New Source": {
        "url": "https://example.com/rss/feed.xml",
        "category": "Category Name",
        "priority": 1  # 1 = high priority, 2 = normal
    },
    # ... existing feeds
}
```

### Adjust AI Keywords

Modify the `AI_KEYWORDS` list to change what articles are considered AI-relevant:

```python
AI_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning',
    # Add your keywords here
]
```

### Adjust SMB Relevance Scoring

Modify the `SMB_KEYWORDS` list to change how SMB relevance is calculated:

```python
SMB_KEYWORDS = [
    'small business', 'smb', 'startup',
    # Add keywords that indicate SMB relevance
]
```

## Scheduling Automation

### macOS/Linux (cron)

Run weekly on Mondays at 8 AM:

```bash
# Edit crontab
crontab -e

# Add this line
0 8 * * 1 cd /path/to/scripts && python ai_digest_generator.py --output ~/Documents/weekly_digest.md
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Weekly, Monday, 8:00 AM
4. Set action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\ai_digest_generator.py --output C:\Documents\weekly_digest.md`

## Workflow Suggestion

1. **Monday morning**: Run the script to generate the weekly digest
2. **Review**: Scan the Top Stories and SMB Spotlight sections
3. **Curate**: Select the most relevant items for your audience
4. **Write**: Add your commentary and insights using the newsletter template
5. **Send**: Distribute your newsletter

## Troubleshooting

### "No articles found"
- Check your internet connection
- Some RSS feeds may be temporarily unavailable
- Try running with `--verbose` flag for more details

### "Module not found" errors
- Ensure you installed dependencies: `pip install feedparser requests python-dateutil`

### Timeout errors
- Some RSS feeds may be slow; the script has a 15-second timeout per feed
- The script will continue even if some feeds fail

## Support

Created for Synergi AI / Insight Driven Business
Contact: jb@insightdriven.business

---

*Last updated: January 30, 2026*
