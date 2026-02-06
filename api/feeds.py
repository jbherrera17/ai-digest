"""GET /api/feeds - Return list of available RSS feeds."""

import json
import os
from http.server import BaseHTTPRequestHandler
from api.shared import RSS_FEEDS

# Try to import Supabase client, fall back to hardcoded feeds if unavailable
USE_DATABASE = os.environ.get('USE_DATABASE', 'false').lower() == 'true'


def get_feeds_from_database():
    """Fetch active feeds from Supabase database."""
    try:
        from api.lib.supabase import get_active_feeds
        feeds = get_active_feeds()
        # Convert to the expected format: {name: {url, category, priority, type}}
        result = {}
        for feed in feeds:
            result[feed['name']] = {
                'url': feed['url'],
                'category': feed['category'],
                'priority': feed.get('priority', 2),
            }
            if feed.get('feed_type'):
                result[feed['name']]['type'] = feed['feed_type']
        return result
    except Exception as e:
        print(f"Database error, falling back to hardcoded feeds: {e}")
        return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        feeds = None

        # Try database first if enabled
        if USE_DATABASE:
            feeds = get_feeds_from_database()

        # Fall back to hardcoded feeds
        if feeds is None:
            feeds = RSS_FEEDS

        self.wfile.write(json.dumps(feeds).encode())
