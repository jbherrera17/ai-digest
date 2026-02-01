"""Shared configuration and utilities for AI Digest serverless functions."""

import re
from datetime import datetime
from dateutil import parser as date_parser

RSS_FEEDS = {
    "TechCrunch AI": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "Tech News",
        "priority": 1,
    },
    "VentureBeat AI": {
        "url": "https://venturebeat.com/category/ai/feed/",
        "category": "Enterprise AI",
        "priority": 1,
    },
    "SiliconANGLE AI": {
        "url": "https://siliconangle.com/category/ai/feed/",
        "category": "Business Tech",
        "priority": 1,
    },
    "MIT Technology Review": {
        "url": "https://www.technologyreview.com/feed/",
        "category": "Research & Policy",
        "priority": 2,
    },
    "Ars Technica AI": {
        "url": "https://arstechnica.com/tag/artificial-intelligence/feed/",
        "category": "Deep Tech",
        "priority": 2,
    },
    "Wired AI": {
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "category": "Tech Culture",
        "priority": 2,
    },
    "The Verge AI": {
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "category": "Consumer Tech",
        "priority": 2,
    },
    "AI Business": {
        "url": "https://aibusiness.com/rss.xml",
        "category": "Enterprise AI",
        "priority": 1,
    },
    "Artificial Intelligence News": {
        "url": "https://www.artificialintelligence-news.com/feed/",
        "category": "AI News",
        "priority": 2,
    },
    "OpenAI Blog": {
        "url": "https://openai.com/blog/rss.xml",
        "category": "Company News",
        "priority": 1,
    },
    "Google AI Blog": {
        "url": "https://blog.google/technology/ai/rss/",
        "category": "Company News",
        "priority": 1,
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


def parse_feed_entries(feed, name, config):
    """Parse feed entries into article dicts."""
    articles = []
    for entry in feed.entries:
        pub_date = None
        for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(entry, date_field) and getattr(entry, date_field):
                try:
                    pub_date = datetime(*getattr(entry, date_field)[:6])
                    break
                except Exception:
                    pass

        if not pub_date:
            for date_str_field in ['published', 'updated', 'created']:
                if hasattr(entry, date_str_field) and getattr(entry, date_str_field):
                    try:
                        pub_date = date_parser.parse(getattr(entry, date_str_field))
                        break
                    except Exception:
                        pass

        if not pub_date:
            pub_date = datetime.now()

        summary = ''
        if hasattr(entry, 'summary'):
            summary = entry.summary
        elif hasattr(entry, 'description'):
            summary = entry.description

        summary = re.sub(r'<[^>]+>', '', summary)
        if len(summary) > 500:
            summary = summary[:500] + '...'

        articles.append({
            'title': entry.get('title', 'No title'),
            'link': entry.get('link', ''),
            'summary': summary.strip(),
            'published': pub_date.isoformat(),
            'published_display': pub_date.strftime('%b %d, %Y'),
            'source': name,
            'category': config['category'],
            'priority': config['priority'],
        })
    return articles


def is_ai_relevant(article):
    text = (article['title'] + ' ' + article['summary']).lower()
    return any(keyword in text for keyword in AI_KEYWORDS)


def calculate_smb_score(article):
    text = (article['title'] + ' ' + article['summary']).lower()
    score = sum(1 for keyword in SMB_KEYWORDS if keyword in text)
    return min(score * 2, 10)


def categorize_article(article):
    text = (article['title'] + ' ' + article['summary']).lower()
    if any(w in text for w in ['funding', 'raise', 'valuation', 'invest', 'billion', 'million']):
        return 'Funding & Deals'
    elif any(w in text for w in ['launch', 'release', 'announce', 'new feature', 'update']):
        return 'Product News'
    elif any(w in text for w in ['research', 'study', 'paper', 'breakthrough']):
        return 'Research'
    elif any(w in text for w in ['regulation', 'law', 'policy', 'government', 'eu', 'congress']):
        return 'Policy & Regulation'
    elif any(w in text for w in ['openai', 'anthropic', 'google', 'microsoft', 'meta', 'nvidia']):
        return 'Big Tech'
    elif any(w in text for w in ['small business', 'smb', 'startup', 'entrepreneur']):
        return 'SMB Focus'
    else:
        return 'General AI News'


def enrich_articles(articles):
    """Filter for AI relevance and add scores/topics."""
    relevant = [a for a in articles if is_ai_relevant(a)]
    for article in relevant:
        article['smb_score'] = calculate_smb_score(article)
        article['topic'] = categorize_article(article)
    return relevant
