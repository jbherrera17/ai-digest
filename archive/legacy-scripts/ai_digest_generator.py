#!/usr/bin/env python3
"""
AI News Digest Generator
========================
Pulls from RSS feeds and generates a weekly AI news digest.

Usage:
    python ai_digest_generator.py                    # Generate digest for past 7 days
    python ai_digest_generator.py --days 3          # Generate digest for past 3 days
    python ai_digest_generator.py --output digest.md # Save to specific file

Created for: Synergi AI / Insight Driven Business
"""

import feedparser
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from collections import defaultdict
import argparse
import re
import os

# ============================================
# RSS FEED CONFIGURATION
# ============================================

RSS_FEEDS = {
    # Primary Tech News Sources
    "TechCrunch AI": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "Tech News",
        "priority": 1
    },
    "VentureBeat AI": {
        "url": "https://venturebeat.com/category/ai/feed/",
        "category": "Enterprise AI",
        "priority": 1
    },
    "SiliconANGLE AI": {
        "url": "https://siliconangle.com/category/ai/feed/",
        "category": "Business Tech",
        "priority": 1
    },
    "MIT Technology Review": {
        "url": "https://www.technologyreview.com/feed/",
        "category": "Research & Policy",
        "priority": 2
    },
    "Ars Technica AI": {
        "url": "https://arstechnica.com/tag/artificial-intelligence/feed/",
        "category": "Deep Tech",
        "priority": 2
    },
    "Wired AI": {
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "category": "Tech Culture",
        "priority": 2
    },
    "The Verge AI": {
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "category": "Consumer Tech",
        "priority": 2
    },

    # AI-Specific Sources
    "AI Business": {
        "url": "https://aibusiness.com/rss.xml",
        "category": "Enterprise AI",
        "priority": 1
    },
    "Artificial Intelligence News": {
        "url": "https://www.artificialintelligence-news.com/feed/",
        "category": "AI News",
        "priority": 2
    },

    # Company Blogs (these may not have RSS, will gracefully fail)
    "OpenAI Blog": {
        "url": "https://openai.com/blog/rss.xml",
        "category": "Company News",
        "priority": 1
    },
    "Google AI Blog": {
        "url": "https://blog.google/technology/ai/rss/",
        "category": "Company News",
        "priority": 1
    },
}

# Keywords to filter for AI-relevant content
AI_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
    'chatgpt', 'gpt', 'openai', 'anthropic', 'claude', 'gemini', 'llm',
    'large language model', 'neural network', 'generative ai', 'gen ai',
    'copilot', 'automation', 'agent', 'agentic', 'model', 'transformer',
    'nvidia', 'gpu', 'training', 'inference', 'prompt', 'rag',
    'small business', 'smb', 'enterprise', 'startup'
]

# Keywords for SMB relevance scoring
SMB_KEYWORDS = [
    'small business', 'smb', 'startup', 'entrepreneur', 'roi',
    'productivity', 'automation', 'workflow', 'tool', 'app',
    'affordable', 'free', 'pricing', 'cost', 'budget'
]


def fetch_feed(name, config):
    """Fetch and parse an RSS feed."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AI Digest Generator/1.0)'
        }
        response = requests.get(config['url'], headers=headers, timeout=15)
        feed = feedparser.parse(response.content)

        if feed.bozo and not feed.entries:
            return []

        articles = []
        for entry in feed.entries:
            # Parse publication date
            pub_date = None
            for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
                if hasattr(entry, date_field) and getattr(entry, date_field):
                    try:
                        pub_date = datetime(*getattr(entry, date_field)[:6])
                        break
                    except:
                        pass

            if not pub_date:
                # Try parsing date string
                for date_str_field in ['published', 'updated', 'created']:
                    if hasattr(entry, date_str_field) and getattr(entry, date_str_field):
                        try:
                            pub_date = date_parser.parse(getattr(entry, date_str_field))
                            break
                        except:
                            pass

            if not pub_date:
                pub_date = datetime.now()

            # Get summary/description
            summary = ''
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'description'):
                summary = entry.description

            # Clean HTML from summary
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary[:500] + '...' if len(summary) > 500 else summary

            articles.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', ''),
                'summary': summary,
                'published': pub_date,
                'source': name,
                'category': config['category'],
                'priority': config['priority']
            })

        return articles

    except Exception as e:
        print(f"  Warning: Could not fetch {name}: {str(e)[:50]}")
        return []


def is_ai_relevant(article):
    """Check if article is AI-relevant based on keywords."""
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


def generate_digest(articles, days=7):
    """Generate the formatted digest."""
    cutoff_date = datetime.now() - timedelta(days=days)

    # Filter recent articles
    recent = [a for a in articles if a['published'] > cutoff_date]

    # Filter for AI relevance
    ai_relevant = [a for a in recent if is_ai_relevant(a)]

    # Add SMB scores and topic categories
    for article in ai_relevant:
        article['smb_score'] = calculate_smb_score(article)
        article['topic'] = categorize_article(article)

    # Sort by priority and date
    ai_relevant.sort(key=lambda x: (x['priority'], -x['published'].timestamp()))

    # Group by topic
    by_topic = defaultdict(list)
    for article in ai_relevant:
        by_topic[article['topic']].append(article)

    # Generate output
    output = []
    output.append("=" * 60)
    output.append("AI NEWS DIGEST")
    output.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    output.append(f"Covering: Past {days} days")
    output.append(f"Articles found: {len(ai_relevant)} AI-relevant articles")
    output.append("=" * 60)
    output.append("")

    # Top Stories (highest priority, most recent)
    top_stories = sorted(ai_relevant, key=lambda x: (x['priority'], -x['published'].timestamp()))[:5]

    output.append("## TOP STORIES")
    output.append("-" * 40)
    for i, article in enumerate(top_stories, 1):
        output.append(f"\n### {i}. {article['title']}")
        output.append(f"Source: {article['source']} | {article['published'].strftime('%b %d, %Y')}")
        output.append(f"Topic: {article['topic']}")
        if article['smb_score'] > 0:
            output.append(f"SMB Relevance: {'★' * article['smb_score']}{'☆' * (10 - article['smb_score'])}")
        output.append(f"\n{article['summary']}")
        output.append(f"\nRead more: {article['link']}")

    output.append("\n")

    # SMB Spotlight (highest SMB scores)
    smb_articles = sorted([a for a in ai_relevant if a['smb_score'] >= 4],
                          key=lambda x: -x['smb_score'])[:3]

    if smb_articles:
        output.append("## SMB AI SPOTLIGHT")
        output.append("-" * 40)
        for article in smb_articles:
            output.append(f"\n### {article['title']}")
            output.append(f"Source: {article['source']} | SMB Score: {article['smb_score']}/10")
            output.append(f"\n{article['summary']}")
            output.append(f"\nRead more: {article['link']}")

    output.append("\n")

    # Quick Hits by Topic
    output.append("## QUICK HITS BY TOPIC")
    output.append("-" * 40)

    topic_order = ['Big Tech', 'Funding & Deals', 'Product News', 'Research',
                   'Policy & Regulation', 'SMB Focus', 'General AI News']

    for topic in topic_order:
        if topic in by_topic and by_topic[topic]:
            output.append(f"\n### {topic}")
            for article in by_topic[topic][:5]:  # Max 5 per topic
                output.append(f"• {article['title']}")
                output.append(f"  {article['source']} | {article['published'].strftime('%b %d')}")
                output.append(f"  {article['link']}")

    output.append("\n")
    output.append("=" * 60)
    output.append("END OF DIGEST")
    output.append("=" * 60)
    output.append("\n")
    output.append("Sources checked:")
    for name in RSS_FEEDS.keys():
        output.append(f"  • {name}")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description='Generate AI News Digest from RSS feeds')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back (default: 7)')
    parser.add_argument('--output', type=str, help='Output file path (default: print to console)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed progress')
    args = parser.parse_args()

    print("=" * 50)
    print("AI NEWS DIGEST GENERATOR")
    print("=" * 50)
    print(f"\nFetching articles from {len(RSS_FEEDS)} sources...")
    print(f"Looking back {args.days} days\n")

    all_articles = []

    for name, config in RSS_FEEDS.items():
        print(f"  Fetching: {name}...", end=" ")
        articles = fetch_feed(name, config)
        all_articles.extend(articles)
        print(f"found {len(articles)} articles")

    print(f"\nTotal articles fetched: {len(all_articles)}")
    print("Generating digest...\n")

    digest = generate_digest(all_articles, days=args.days)

    if args.output:
        output_path = args.output
        with open(output_path, 'w') as f:
            f.write(digest)
        print(f"Digest saved to: {output_path}")
    else:
        print(digest)

    print("\nDone!")


if __name__ == "__main__":
    main()
