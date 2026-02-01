"""POST /api/fetch-feed - Fetch a single RSS feed and return enriched articles.

Request body: { "name": "TechCrunch AI", "days": 7 }
Response: { "success": true, "articles": [...], "error": null }

Called in parallel from the frontend, one per feed.
"""

import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
import feedparser
import requests
from api.shared import RSS_FEEDS, parse_feed_entries, enrich_articles


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        name = body.get('name', '')
        days = body.get('days', 7)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if name not in RSS_FEEDS:
            self.wfile.write(json.dumps({
                'success': False, 'articles': [], 'error': f'Unknown feed: {name}'
            }).encode())
            return

        config = RSS_FEEDS[name]
        cutoff = datetime.now() - timedelta(days=days)

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            resp = requests.get(config['url'], headers=headers, timeout=8)
            feed = feedparser.parse(resp.content)

            if feed.bozo and not feed.entries:
                self.wfile.write(json.dumps({
                    'success': False, 'articles': [], 'error': 'Feed parsing error'
                }).encode())
                return

            articles = parse_feed_entries(feed, name, config)
            # Filter by date
            articles = [a for a in articles
                        if datetime.fromisoformat(a['published']) > cutoff]
            # Enrich with AI relevance, SMB scores, topics
            articles = enrich_articles(articles)

            self.wfile.write(json.dumps({
                'success': True, 'articles': articles, 'error': None
            }).encode())

        except requests.exceptions.Timeout:
            self.wfile.write(json.dumps({
                'success': False, 'articles': [], 'error': 'Timeout'
            }).encode())
        except Exception as e:
            self.wfile.write(json.dumps({
                'success': False, 'articles': [], 'error': str(e)[:100]
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
