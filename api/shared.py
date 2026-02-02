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
    # --- Substack Subscriptions ---
    "Nate's Newsletter": {
        "url": "https://natesnewsletter.substack.com/feed",
        "category": "Substack",
        "priority": 2,
        "type": "newsletter",
    },
    "Sergei AI": {
        "url": "https://sergeiai.substack.com/feed",
        "category": "Substack",
        "priority": 2,
        "type": "newsletter",
    },
    "The Algorithmic Bridge": {
        "url": "https://www.thealgorithmicbridge.com/feed",
        "category": "Substack",
        "priority": 2,
        "type": "newsletter",
    },
    "ByteByteGo": {
        "url": "https://blog.bytebytego.com/feed",
        "category": "Substack",
        "priority": 2,
        "type": "newsletter",
    },
    "Concept Bureau": {
        "url": "https://conceptbureau.substack.com/feed",
        "category": "Substack",
        "priority": 2,
        "type": "newsletter",
    },
    "AI Search": {
        "url": "https://aisearch.substack.com/feed",
        "category": "Substack",
        "priority": 2,
        "type": "newsletter",
    },
    "AI Supremacy": {
        "url": "https://www.ai-supremacy.com/feed",
        "category": "Substack",
        "priority": 2,
        "type": "newsletter",
    },
    "Latent Space": {
        "url": "https://www.latent.space/feed",
        "category": "Substack",
        "priority": 1,
        "type": "newsletter",
    },
    "Excellent Prompts": {
        "url": "https://excellentprompts.substack.com/feed",
        "category": "Substack",
        "priority": 2,
        "type": "newsletter",
    },
    # --- Medium Follows ---
    "Towards AI (Medium)": {
        "url": "https://medium.com/feed/towards-artificial-intelligence",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    "UX Collective (Medium)": {
        "url": "https://medium.com/feed/ux-collective",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    "Gaurav Jain (Medium)": {
        "url": "https://medium.com/feed/@gauravjain",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    "AI Advances (Medium)": {
        "url": "https://medium.com/feed/ai-advances",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    "Generative AI (Medium)": {
        "url": "https://medium.com/feed/generative-ai",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    "UX Planet (Medium)": {
        "url": "https://medium.com/feed/ux-planet",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    "Entrepreneurship Handbook (Medium)": {
        "url": "https://medium.com/feed/entrepreneurs-handbook",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    "AI in Plain English (Medium)": {
        "url": "https://medium.com/feed/ai-in-plain-english",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    "Alberto Romero (Medium)": {
        "url": "https://medium.com/feed/@albertoromgar",
        "category": "Medium",
        "priority": 2,
        "type": "newsletter",
    },
    # --- Company Blogs: AI Labs ---
    "Anthropic Blog": {
        "url": "https://www.anthropic.com/research/rss.xml",
        "category": "Company Blog",
        "priority": 1,
        "type": "blog",
    },
    "Meta AI Blog": {
        "url": "https://ai.meta.com/blog/rss/",
        "category": "Company Blog",
        "priority": 1,
        "type": "blog",
    },
    "Microsoft AI Blog": {
        "url": "https://blogs.microsoft.com/ai/feed/",
        "category": "Company Blog",
        "priority": 1,
        "type": "blog",
    },
    "Amazon AI Blog": {
        "url": "https://aws.amazon.com/blogs/machine-learning/feed/",
        "category": "Company Blog",
        "priority": 2,
        "type": "blog",
    },
    "Apple Machine Learning": {
        "url": "https://machinelearning.apple.com/rss.xml",
        "category": "Company Blog",
        "priority": 2,
        "type": "blog",
    },
    # --- Company Blogs: AI Infrastructure ---
    "NVIDIA Blog": {
        "url": "https://blogs.nvidia.com/feed/",
        "category": "AI Infrastructure",
        "priority": 1,
        "type": "blog",
    },
    "AMD AI Blog": {
        "url": "https://community.amd.com/t5/ai/bg-p/amd-ai/label-name/blog",
        "category": "AI Infrastructure",
        "priority": 2,
        "type": "blog",
    },
    # --- Company Blogs: AI-First Companies ---
    "Hugging Face Blog": {
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "AI Platform",
        "priority": 1,
        "type": "blog",
    },
    "Stability AI Blog": {
        "url": "https://stability.ai/blog/rss.xml",
        "category": "AI Platform",
        "priority": 2,
        "type": "blog",
    },
    "Cohere Blog": {
        "url": "https://cohere.com/blog/rss.xml",
        "category": "AI Platform",
        "priority": 2,
        "type": "blog",
    },
    "Mistral AI Blog": {
        "url": "https://mistral.ai/feed.xml",
        "category": "AI Platform",
        "priority": 2,
        "type": "blog",
    },
    "Perplexity Blog": {
        "url": "https://www.perplexity.ai/hub/blog/rss.xml",
        "category": "AI Platform",
        "priority": 2,
        "type": "blog",
    },
    # --- Company Blogs: Enterprise / Productivity ---
    "Salesforce AI Blog": {
        "url": "https://blog.salesforceairesearch.com/rss/",
        "category": "Enterprise AI",
        "priority": 2,
        "type": "blog",
    },
    "Notion AI Blog": {
        "url": "https://www.notion.so/blog/rss.xml",
        "category": "Productivity AI",
        "priority": 2,
        "type": "blog",
    },
    "Canva AI Blog": {
        "url": "https://www.canva.dev/blog/engineering/feed.xml",
        "category": "Productivity AI",
        "priority": 2,
        "type": "blog",
    },
    # --- Company Blogs: Cloud Platforms ---
    "Google Cloud AI Blog": {
        "url": "https://cloud.google.com/blog/products/ai-machine-learning/rss",
        "category": "Cloud AI",
        "priority": 2,
        "type": "blog",
    },
    "AWS Machine Learning Blog": {
        "url": "https://aws.amazon.com/blogs/aws/category/artificial-intelligence/feed/",
        "category": "Cloud AI",
        "priority": 2,
        "type": "blog",
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

# --- ICP Pain Point Matching ---
# Keywords from each ICP mapped to specific, actionable SMB impact statements.
# When an article matches these keywords, the impact text addresses real pain points
# from Coaches/Consultants, Professional Services, Healthcare, and Manufacturing ICPs.

ICP_PAIN_SIGNALS = [
    {
        'keywords': ['content', 'marketing', 'writing', 'blog', 'newsletter', 'social media', 'thought leadership', 'brand'],
        'smb_impact': 'Coaches and consultants trapped on the content marketing treadmill should evaluate this for automating thought leadership — freeing time from admin-heavy content creation while maintaining an authentic voice.',
    },
    {
        'keywords': ['scheduling', 'calendar', 'booking', 'appointment', 'onboarding', 'intake', 'client management', 'crm'],
        'smb_impact': 'For practices drowning in admin — from client onboarding to scheduling — this could reduce the manual overhead that caps revenue at billable hours. Healthcare clinics facing intake backlogs and coaching practices with leads slipping through cracks should watch closely.',
    },
    {
        'keywords': ['automation', 'workflow', 'process', 'automate', 'efficiency', 'streamline', 'productivity'],
        'smb_impact': 'This directly addresses the #1 pain across SMBs: manual repetitive processes. Professional service firms losing margin to non-billable admin, manufacturers drowning in spreadsheets, and coaches working late nights on operations should assess how this reduces hands-on busywork.',
    },
    {
        'keywords': ['compliance', 'regulation', 'hipaa', 'gdpr', 'audit', 'privacy', 'security', 'data protection'],
        'smb_impact': 'For healthcare practices navigating HIPAA, law firms managing compliance complexity, and manufacturers facing ISO requirements — this impacts your regulatory burden directly. Monitor whether new compliance tools emerge or if new rules add overhead to your AI adoption.',
    },
    {
        'keywords': ['hiring', 'staffing', 'talent', 'workforce', 'employee', 'labor', 'recruitment', 'retention', 'team'],
        'smb_impact': 'SMBs struggling to scale without adding headcount take note. Coaches capped by 1:1 sessions, professional services firms with partners working non-billable hours, and manufacturers who can\'t find skilled machinists could use AI to bridge staffing gaps without ballooning payroll.',
    },
    {
        'keywords': ['cost', 'pricing', 'affordable', 'budget', 'margin', 'revenue', 'profit', 'roi', 'subscription', 'free tier'],
        'smb_impact': 'Margin pressure is real across SMBs — from professional services firms watching labor costs erode profits to manufacturers with tight margins on custom work. Evaluate whether this offers measurable ROI at a price point that works without enterprise budgets.',
    },
    {
        'keywords': ['chatbot', 'customer service', 'support', 'conversation', 'assistant', 'agent', 'virtual assistant'],
        'smb_impact': 'Practices losing leads to inconsistent follow-up and clinics with overwhelmed receptionists should evaluate AI assistants carefully. The key concern across ICPs: will it feel impersonal? Look for solutions that augment your team rather than replace the human touch your clients expect.',
    },
    {
        'keywords': ['document', 'report', 'paperwork', 'filing', 'template', 'contract', 'invoice'],
        'smb_impact': 'Document-heavy businesses — law firms buried in case files, accounting firms with manual reporting, healthcare practices with charting backlogs, manufacturers tracking work-in-progress on whiteboards — this could cut hours of non-billable paperwork per week.',
    },
    {
        'keywords': ['scale', 'scaling', 'growth', 'expand', 'grow'],
        'smb_impact': 'The central challenge across SMBs: growing without proportional cost increases. Coaches want to move from 1:1 to 1:many. Professional services need more throughput without more hires. Manufacturers need capacity without overtime. Assess how this helps you scale smartly.',
    },
    {
        'keywords': ['integration', 'api', 'platform', 'connect', 'ecosystem', 'plugin', 'app store'],
        'smb_impact': 'Siloed tools and poor integration plague SMBs — from disconnected practice management systems to manufacturing equipment that doesn\'t talk to each other. Look for whether this connects to tools you already use rather than creating another data island.',
    },
    {
        'keywords': ['patient', 'health', 'clinical', 'medical', 'care', 'diagnosis', 'treatment', 'ehr'],
        'smb_impact': 'Small healthcare organizations spending evenings charting and scrambling before audits should assess this carefully. The promise: more time for patient care, less paperwork. The concern: patient data safety and maintaining trust. Look for HIPAA-ready, explainable AI.',
    },
    {
        'keywords': ['manufacturing', 'production', 'supply chain', 'inventory', 'logistics', 'warehouse', 'factory', 'industrial'],
        'smb_impact': 'Small manufacturers dealing with production bottlenecks, excess downtime, and legacy equipment should evaluate this. The goal: predictable output, lower scrap rates, and better visibility into real-time costs — without disrupting current operations during adoption.',
    },
]


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
    """Generate 'What it Means' content based on article topic and ICP pain points."""
    topic = article.get('topic', 'General AI News')
    templates = IMPACT_TEMPLATES.get(topic, IMPACT_TEMPLATES['General AI News'])
    general = templates['general']

    # Try to match article content to specific ICP pain points
    text = (article['title'] + ' ' + article.get('summary', '')).lower()
    matched_impacts = []
    for signal in ICP_PAIN_SIGNALS:
        if any(kw in text for kw in signal['keywords']):
            matched_impacts.append(signal['smb_impact'])

    if matched_impacts:
        # Use the most specific ICP match (first matched)
        smb = matched_impacts[0]
    else:
        # Fall back to topic-based template
        smb = templates['smb']

    return {
        'general_impact': general,
        'smb_impact': smb,
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
