#!/usr/bin/env python3
"""
AI News Digest Web App
======================
A web interface for generating AI news digests from RSS feeds.

Run with: python app.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template, jsonify, request, Response
import feedparser
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from collections import defaultdict
import re
import json
import threading

app = Flask(__name__)

# ============================================
# RSS FEED CONFIGURATION
# ============================================

RSS_FEEDS = {
    "TechCrunch AI": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "Tech News",
        "priority": 1,
        "enabled": True
    },
    "VentureBeat AI": {
        "url": "https://venturebeat.com/category/ai/feed/",
        "category": "Enterprise AI",
        "priority": 1,
        "enabled": True
    },
    "SiliconANGLE AI": {
        "url": "https://siliconangle.com/category/ai/feed/",
        "category": "Business Tech",
        "priority": 1,
        "enabled": True
    },
    "MIT Technology Review": {
        "url": "https://www.technologyreview.com/feed/",
        "category": "Research & Policy",
        "priority": 2,
        "enabled": True
    },
    "Ars Technica AI": {
        "url": "https://arstechnica.com/tag/artificial-intelligence/feed/",
        "category": "Deep Tech",
        "priority": 2,
        "enabled": True
    },
    "Wired AI": {
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "category": "Tech Culture",
        "priority": 2,
        "enabled": True
    },
    "The Verge AI": {
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "category": "Consumer Tech",
        "priority": 2,
        "enabled": True
    },
    "AI Business": {
        "url": "https://aibusiness.com/rss.xml",
        "category": "Enterprise AI",
        "priority": 1,
        "enabled": True
    },
    "Artificial Intelligence News": {
        "url": "https://www.artificialintelligence-news.com/feed/",
        "category": "AI News",
        "priority": 2,
        "enabled": True
    },
    "OpenAI Blog": {
        "url": "https://openai.com/blog/rss.xml",
        "category": "Company News",
        "priority": 1,
        "enabled": True
    },
    "Google AI Blog": {
        "url": "https://blog.google/technology/ai/rss/",
        "category": "Company News",
        "priority": 1,
        "enabled": True
    },
}

AI_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
    'chatgpt', 'gpt', 'openai', 'anthropic', 'claude', 'gemini', 'llm',
    'large language model', 'neural network', 'generative ai', 'gen ai',
    'copilot', 'automation', 'agent', 'agentic', 'model', 'transformer',
    'nvidia', 'gpu', 'training', 'inference', 'prompt', 'rag',
    'small business', 'smb', 'enterprise', 'startup'
]

SMB_KEYWORDS = [
    'small business', 'smb', 'startup', 'entrepreneur', 'roi',
    'productivity', 'automation', 'workflow', 'tool', 'app',
    'affordable', 'free', 'pricing', 'cost', 'budget'
]

# Global state for progress tracking
fetch_progress = {
    'status': 'idle',
    'current': 0,
    'total': 0,
    'current_source': '',
    'articles': [],
    'errors': []
}


def fetch_feed(name, config):
    """Fetch and parse an RSS feed."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(config['url'], headers=headers, timeout=15)
        feed = feedparser.parse(response.content)

        if feed.bozo and not feed.entries:
            return [], f"Feed parsing error"

        articles = []
        for entry in feed.entries:
            pub_date = None
            for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
                if hasattr(entry, date_field) and getattr(entry, date_field):
                    try:
                        pub_date = datetime(*getattr(entry, date_field)[:6])
                        break
                    except:
                        pass

            if not pub_date:
                for date_str_field in ['published', 'updated', 'created']:
                    if hasattr(entry, date_str_field) and getattr(entry, date_str_field):
                        try:
                            pub_date = date_parser.parse(getattr(entry, date_str_field))
                            break
                        except:
                            pass

            if not pub_date:
                pub_date = datetime.now()

            summary = ''
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'description'):
                summary = entry.description

            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary[:500] + '...' if len(summary) > 500 else summary

            articles.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', ''),
                'summary': summary.strip(),
                'published': pub_date.isoformat(),
                'published_display': pub_date.strftime('%b %d, %Y'),
                'source': name,
                'category': config['category'],
                'priority': config['priority']
            })

        return articles, None

    except requests.exceptions.Timeout:
        return [], "Timeout"
    except Exception as e:
        return [], str(e)[:50]


def is_ai_relevant(article):
    """Check if article is AI-relevant."""
    text = (article['title'] + ' ' + article['summary']).lower()
    return any(keyword in text for keyword in AI_KEYWORDS)


def calculate_smb_score(article):
    """Calculate SMB relevance score (0-10)."""
    text = (article['title'] + ' ' + article['summary']).lower()
    score = sum(1 for keyword in SMB_KEYWORDS if keyword in text)
    return min(score * 2, 10)


def categorize_article(article):
    """Categorize article by topic."""
    text = (article['title'] + ' ' + article['summary']).lower()

    if any(word in text for word in ['funding', 'raise', 'valuation', 'invest', 'billion', 'million']):
        return 'Funding & Deals'
    elif any(word in text for word in ['launch', 'release', 'announce', 'new feature', 'update']):
        return 'Product News'
    elif any(word in text for word in ['research', 'study', 'paper', 'breakthrough']):
        return 'Research'
    elif any(word in text for word in ['regulation', 'law', 'policy', 'government', 'eu', 'congress']):
        return 'Policy & Regulation'
    elif any(word in text for word in ['openai', 'anthropic', 'google', 'microsoft', 'meta', 'nvidia']):
        return 'Big Tech'
    elif any(word in text for word in ['small business', 'smb', 'startup', 'entrepreneur']):
        return 'SMB Focus'
    else:
        return 'General AI News'


def fetch_all_feeds(days=7, selected_feeds=None):
    """Fetch all feeds and return processed articles."""
    global fetch_progress

    feeds_to_fetch = {k: v for k, v in RSS_FEEDS.items()
                      if v['enabled'] and (selected_feeds is None or k in selected_feeds)}

    fetch_progress['status'] = 'fetching'
    fetch_progress['current'] = 0
    fetch_progress['total'] = len(feeds_to_fetch)
    fetch_progress['articles'] = []
    fetch_progress['errors'] = []

    cutoff_date = datetime.now() - timedelta(days=days)
    all_articles = []

    for i, (name, config) in enumerate(feeds_to_fetch.items()):
        fetch_progress['current'] = i + 1
        fetch_progress['current_source'] = name

        articles, error = fetch_feed(name, config)

        if error:
            fetch_progress['errors'].append({'source': name, 'error': error})
        else:
            # Filter by date
            for article in articles:
                pub_date = datetime.fromisoformat(article['published'])
                if pub_date > cutoff_date:
                    all_articles.append(article)

    # Process articles
    ai_relevant = [a for a in all_articles if is_ai_relevant(a)]

    for article in ai_relevant:
        article['smb_score'] = calculate_smb_score(article)
        article['topic'] = categorize_article(article)

    # Sort by date (newest first)
    ai_relevant.sort(key=lambda x: x['published'], reverse=True)

    fetch_progress['status'] = 'complete'
    fetch_progress['articles'] = ai_relevant

    return ai_relevant


# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html', feeds=RSS_FEEDS)


@app.route('/api/feeds')
def get_feeds():
    """Get list of available feeds."""
    return jsonify(RSS_FEEDS)


@app.route('/api/generate', methods=['POST'])
def generate_digest():
    """Generate digest from feeds."""
    data = request.json or {}
    days = data.get('days', 7)
    selected_feeds = data.get('feeds', None)

    articles = fetch_all_feeds(days=days, selected_feeds=selected_feeds)

    # Group by topic
    by_topic = defaultdict(list)
    for article in articles:
        by_topic[article['topic']].append(article)

    # Get top stories
    top_stories = sorted(articles, key=lambda x: (x['priority'], x['published']))[:5]

    # Get SMB spotlight
    smb_spotlight = sorted([a for a in articles if a['smb_score'] >= 4],
                           key=lambda x: -x['smb_score'])[:3]

    return jsonify({
        'success': True,
        'stats': {
            'total_articles': len(articles),
            'sources_checked': fetch_progress['total'],
            'errors': fetch_progress['errors'],
            'generated_at': datetime.now().isoformat()
        },
        'top_stories': top_stories,
        'smb_spotlight': smb_spotlight,
        'by_topic': dict(by_topic),
        'all_articles': articles
    })


@app.route('/api/progress')
def get_progress():
    """Get current fetch progress."""
    return jsonify(fetch_progress)


@app.route('/api/export/markdown', methods=['POST'])
def export_markdown():
    """Export digest as markdown."""
    data = request.json or {}
    articles = data.get('articles', [])
    top_stories = data.get('top_stories', [])
    smb_spotlight = data.get('smb_spotlight', [])

    md = []
    md.append("# AI News Digest")
    md.append(f"\n*Generated: {datetime.now().strftime('%B %d, %Y')}*\n")

    md.append("\n## Top Stories\n")
    for i, article in enumerate(top_stories, 1):
        md.append(f"### {i}. {article['title']}")
        md.append(f"*{article['source']} | {article['published_display']}*\n")
        md.append(f"{article['summary']}\n")
        md.append(f"[Read more]({article['link']})\n")

    if smb_spotlight:
        md.append("\n## SMB AI Spotlight\n")
        for article in smb_spotlight:
            md.append(f"### {article['title']}")
            md.append(f"*{article['source']} | SMB Score: {article['smb_score']}/10*\n")
            md.append(f"{article['summary']}\n")
            md.append(f"[Read more]({article['link']})\n")

    md.append("\n## Quick Hits\n")
    for article in articles[:10]:
        md.append(f"- **{article['title']}** - {article['source']} ([link]({article['link']}))")

    content = "\n".join(md)

    return Response(
        content,
        mimetype='text/markdown',
        headers={'Content-Disposition': 'attachment; filename=ai_digest.md'}
    )


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("AI NEWS DIGEST WEB APP")
    print("=" * 50)
    print("\nStarting server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
