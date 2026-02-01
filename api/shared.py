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
    "The AI Newsletter (Towards AI)": {
        "url": "https://pub.towardsai.net/feed",
        "category": "Newsletter",
        "priority": 2,
        "type": "newsletter",
    },
    "Import AI Newsletter": {
        "url": "https://importai.substack.com/feed",
        "category": "Newsletter",
        "priority": 2,
        "type": "newsletter",
    },
    "The Batch (deeplearning.ai)": {
        "url": "https://www.deeplearning.ai/the-batch/feed/",
        "category": "Newsletter",
        "priority": 1,
        "type": "newsletter",
    },
    "TLDR AI": {
        "url": "https://tldr.tech/ai/rss",
        "category": "Newsletter",
        "priority": 1,
        "type": "newsletter",
    },
    "Ben's Bites": {
        "url": "https://bensbites.beehiiv.com/feed",
        "category": "Newsletter",
        "priority": 2,
        "type": "newsletter",
    },
    "The Neuron": {
        "url": "https://www.theneurondaily.com/feed",
        "category": "Newsletter",
        "priority": 2,
        "type": "newsletter",
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


VIRAL_KEYWORDS = [
    'breakthrough', 'shocking', 'disrupting', 'revolutionary', 'game-changing',
    'billion', 'millions of users', 'viral', 'banned', 'leaked', 'controversy',
    'replaced', 'eliminated', 'threatens', 'surpasses', 'dominates', 'record',
    'unprecedented', 'first ever', 'massive', 'exploding', 'everyone',
    'jobs', 'layoffs', 'regulation', 'safety', 'risk', 'danger',
    'open source', 'free', 'agi', 'singularity', 'sentient',
]

IMPACT_TEMPLATES = {
    'Big Tech': {
        'general': 'Major tech companies are shaping the AI landscape, influencing product ecosystems, competitive dynamics, and the pace of innovation across the industry.',
        'smb': 'Big tech AI moves often trickle down as new tools, APIs, and platform features that SMBs can leverage. Watch for new capabilities becoming available at lower price points.',
    },
    'Funding & Deals': {
        'general': 'Investment activity signals where the market sees growth potential and which AI capabilities are maturing toward commercial viability.',
        'smb': 'Funded startups often launch affordable or freemium AI tools targeting underserved markets. New entrants can mean more choices and competitive pricing for small businesses.',
    },
    'Product News': {
        'general': 'New AI product launches and updates expand what\'s possible with current technology and may shift user expectations across the market.',
        'smb': 'New product releases often include SMB-friendly tiers. Evaluate whether these tools can automate manual processes or improve customer experience in your business.',
    },
    'Research': {
        'general': 'Research breakthroughs lay the groundwork for next-generation AI capabilities that will eventually reach commercial products.',
        'smb': 'While research may seem distant, breakthroughs often become accessible tools within 12-18 months. Stay aware to plan ahead for adoption opportunities.',
    },
    'Policy & Regulation': {
        'general': 'Regulatory developments will define how AI can be deployed, affecting compliance requirements and market access for all organizations.',
        'smb': 'New regulations can create compliance burdens but also level the playing field. SMBs should monitor requirements that may affect their AI tool usage or data handling.',
    },
    'SMB Focus': {
        'general': 'AI solutions specifically targeting smaller organizations are making advanced capabilities accessible without enterprise budgets.',
        'smb': 'These developments are directly relevant to your business. Evaluate featured tools for immediate ROI potential and competitive advantage in your market.',
    },
    'General AI News': {
        'general': 'Broader AI developments reflect the evolving landscape and can signal emerging trends worth monitoring.',
        'smb': 'General AI trends often reveal opportunities for early adopters. Consider how these developments might apply to your specific industry or workflow.',
    },
}


def extract_key_bullets(article):
    """Extract 2-3 key bullet points from the article summary."""
    summary = article.get('summary', '')
    if not summary:
        return []

    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', summary.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) <= 3:
        return sentences if sentences else [summary[:200]]

    # Return first 3 meaningful sentences
    return sentences[:3]


def calculate_viral_score(article):
    """Score 0-10 for how viral/trending the topic is."""
    text = (article['title'] + ' ' + article['summary']).lower()
    score = sum(1 for kw in VIRAL_KEYWORDS if kw in text)
    return min(score * 2, 10)


def generate_impact(article):
    """Generate 'What it Means' content based on article topic."""
    topic = article.get('topic', 'General AI News')
    templates = IMPACT_TEMPLATES.get(topic, IMPACT_TEMPLATES['General AI News'])
    return {
        'general_impact': templates['general'],
        'smb_impact': templates['smb'],
    }


def generate_viral_suggestions(article):
    """If article is viral, suggest content creation topics."""
    if article.get('viral_score', 0) < 4:
        return None

    title = article['title']
    topic = article.get('topic', 'General AI News')
    base_topics = []

    text = (title + ' ' + article.get('summary', '')).lower()

    if any(w in text for w in ['tool', 'app', 'product', 'launch', 'release']):
        base_topics.append(f"Review/comparison: How does this new tool stack up for small businesses?")
        base_topics.append(f"Tutorial: Getting started with the AI tool mentioned in '{title[:60]}'")
    if any(w in text for w in ['jobs', 'layoffs', 'replace', 'automate']):
        base_topics.append("Opinion piece: What AI automation means for your industry's workforce")
        base_topics.append("Guide: How SMBs can use AI to augment (not replace) their teams")
    if any(w in text for w in ['regulation', 'policy', 'law', 'ban', 'safety']):
        base_topics.append("Explainer: What new AI regulations mean for small business owners")
        base_topics.append("Checklist: Is your business AI-compliant?")
    if any(w in text for w in ['funding', 'billion', 'valuation', 'invest']):
        base_topics.append("Analysis: What this funding round signals for the AI market")
        base_topics.append("Listicle: Affordable AI alternatives for budget-conscious businesses")
    if any(w in text for w in ['breakthrough', 'research', 'paper', 'model']):
        base_topics.append(f"Simplified explainer: What this AI breakthrough means in plain English")
        base_topics.append("Prediction piece: How this research will affect everyday business tools")

    if not base_topics:
        base_topics.append(f"Hot take: Your perspective on '{title[:60]}'")
        base_topics.append(f"Listicle: {topic} trends SMBs need to watch right now")

    return base_topics[:3]


def enrich_articles(articles):
    """Filter for AI relevance and add scores/topics."""
    relevant = [a for a in articles if is_ai_relevant(a)]
    for article in relevant:
        article['smb_score'] = calculate_smb_score(article)
        article['topic'] = categorize_article(article)
        article['key_bullets'] = extract_key_bullets(article)
        article['viral_score'] = calculate_viral_score(article)
        article['impact'] = generate_impact(article)
        article['content_suggestions'] = generate_viral_suggestions(article)
    return relevant
