"""POST /api/summarize - Generate AI-powered summaries using Claude.

Request body: {
    "url": "https://example.com/article",
    "type": "tldr" | "executive",
    "title": "Article Title"
}

Response: {
    "success": true,
    "summary": "Generated summary in HTML format",
    "error": null
}
"""

import json
import os
from http.server import BaseHTTPRequestHandler
import anthropic
import requests
from bs4 import BeautifulSoup


def fetch_article_content(url):
    """Fetch and extract main content from article URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()

        # Try to find main content
        main_content = None
        for selector in ['article', 'main', '.post-content', '.article-content', '.entry-content']:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.find('body')

        # Get text
        text = main_content.get_text(separator='\n', strip=True) if main_content else ''

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # Limit to first 4000 words to avoid token limits
        words = text.split()
        if len(words) > 4000:
            text = ' '.join(words[:4000]) + '...'

        return text

    except Exception as e:
        raise Exception(f"Failed to fetch article: {str(e)}")


def generate_tldr_summary(article_text, title, url):
    """Generate a TL;DR summary using Claude."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Generate a concise TL;DR summary of this article in HTML format.

Article Title: {title}
Article URL: {url}

Article Content:
{article_text}

Create a brief summary with:
1. A "Quick Summary" section with 3-5 key bullet points
2. Keep it concise - focus on the most important takeaways
3. Use clear, simple language

Format your response as clean HTML with:
- <h4> for section headers
- <ul> and <li> for bullet points
- <p> for paragraphs

Do not include the article title in your response (it's already shown in the modal).
"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def generate_executive_summary(article_text, title, url):
    """Generate an executive summary using Claude."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Generate a comprehensive executive summary of this article in HTML format.

Article Title: {title}
Article URL: {url}

Article Content:
{article_text}

Create a detailed executive summary with:
1. **Overview**: 3-5 bullet points covering the main points
2. **Key Insights**: The most important findings or developments
3. **Business Impact**: How this affects businesses, particularly SMBs
4. **Strategic Implications**: What decision-makers should know
5. **Actionable Takeaways**: Concrete next steps or considerations

Format your response as clean HTML with:
- <h4> for section headers
- <ul> and <li> for bullet points
- <p> for paragraphs
- <strong> for emphasis where appropriate

Do not include the article title in your response (it's already shown in the modal).
Focus on providing value for business decision-makers, especially small and medium business owners.
"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        url = body.get('url', '')
        summary_type = body.get('type', 'tldr')
        title = body.get('title', 'Article')

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if not url:
            self.wfile.write(json.dumps({
                'success': False,
                'summary': '',
                'error': 'URL is required'
            }).encode())
            return

        try:
            # Fetch article content
            article_text = fetch_article_content(url)

            if not article_text:
                raise Exception("No content could be extracted from the article")

            # Generate summary based on type
            if summary_type == 'tldr':
                summary = generate_tldr_summary(article_text, title, url)
            else:
                summary = generate_executive_summary(article_text, title, url)

            # Add source link at the bottom
            summary += f'''
                <p style="margin-top: 20px; padding-top: 16px; border-top: 1px solid #e9ecef; font-size: 0.85rem;">
                    <a href="{url}" target="_blank" style="color: #667eea; text-decoration: none;">Read full article →</a>
                </p>
            '''

            self.wfile.write(json.dumps({
                'success': True,
                'summary': summary,
                'error': None
            }).encode())

        except Exception as e:
            self.wfile.write(json.dumps({
                'success': False,
                'summary': '',
                'error': str(e)
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
