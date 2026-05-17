# AI News Digest Web App

A beautiful web interface for generating AI news digests from RSS feeds.

![Screenshot](screenshot.png)

## Quick Start

### macOS / Linux
```bash
cd ai_digest_webapp
chmod +x start.sh
./start.sh
```

### Windows
```bash
cd ai_digest_webapp
start.bat
```

Then open your browser to: **http://localhost:5000**

## Features

- **11+ RSS Sources** - TechCrunch, VentureBeat, SiliconANGLE, MIT Tech Review, and more
- **Smart Filtering** - Automatically filters for AI-relevant content
- **SMB Scoring** - Rates articles for small business relevance (★ rating)
- **Topic Categorization** - Organizes by Big Tech, Funding, Product News, Research, Policy
- **Export Options** - Download as Markdown or copy to clipboard
- **Beautiful UI** - Modern, responsive design

## Manual Installation

If the startup scripts don't work:

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

## How to Use

1. **Select Time Range** - Choose how far back to look (24 hours to 2 weeks)
2. **Choose Sources** - Select which RSS feeds to pull from
3. **Generate** - Click the button and wait for feeds to be fetched
4. **Browse Results** - View Top Stories, SMB Spotlight, or browse by Topic
5. **Export** - Download as Markdown or copy to clipboard

## Adding Custom RSS Feeds

Edit `app.py` and add to the `RSS_FEEDS` dictionary:

```python
RSS_FEEDS = {
    "Your New Feed": {
        "url": "https://example.com/feed.xml",
        "category": "Category Name",
        "priority": 1,  # 1 = high, 2 = normal
        "enabled": True
    },
    # ... existing feeds
}
```

## File Structure

```
ai_digest_webapp/
├── app.py              # Flask backend
├── templates/
│   └── index.html      # Frontend UI
├── requirements.txt    # Python dependencies
├── start.sh           # macOS/Linux startup
├── start.bat          # Windows startup
└── README.md          # This file
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/api/feeds` | GET | List available feeds |
| `/api/generate` | POST | Generate digest |
| `/api/export/markdown` | POST | Export as Markdown |

## Requirements

- Python 3.8+
- Internet connection (to fetch RSS feeds)

## Troubleshooting

**"No articles found"**
- Check your internet connection
- Some feeds may be temporarily unavailable
- Try selecting different sources

**"Module not found"**
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt`

**Port 5000 already in use**
- Another app is using port 5000
- Edit `app.py` and change `port=5000` to another port (e.g., 5001)

---

Built for **Synergi AI / Insight Driven Business**
