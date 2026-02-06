"""Admin API endpoints for feed management."""

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.supabase import (
    get_all_feeds, get_feed_by_id, create_feed,
    update_feed, delete_feed, toggle_feed_active
)


def verify_admin_token(headers):
    """Verify admin authentication token."""
    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header[7:]
    # Check against environment variable for simple auth
    # In production, use Supabase Auth JWT verification
    admin_token = os.environ.get('ADMIN_API_TOKEN', '')
    if not admin_token:
        # If no token configured, allow access (dev mode)
        return True
    return token == admin_token


class handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_json(self, message, status=400):
        self.send_json({'error': message}, status)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        if not verify_admin_token(self.headers):
            self.send_error_json('Unauthorized', 401)
            return

        try:
            parsed = urlparse(self.path)
            path_parts = parsed.path.strip('/').split('/')

            # GET /api/admin/feeds - List all feeds
            if len(path_parts) == 3:
                feeds = get_all_feeds()
                self.send_json({'feeds': feeds, 'count': len(feeds)})

            # GET /api/admin/feeds/:id - Get single feed
            elif len(path_parts) == 4:
                feed_id = path_parts[3]
                feed = get_feed_by_id(feed_id)
                if feed:
                    self.send_json(feed)
                else:
                    self.send_error_json('Feed not found', 404)
            else:
                self.send_error_json('Invalid path', 400)

        except Exception as e:
            self.send_error_json(str(e), 500)

    def do_POST(self):
        if not verify_admin_token(self.headers):
            self.send_error_json('Unauthorized', 401)
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            parsed = urlparse(self.path)
            path_parts = parsed.path.strip('/').split('/')

            # POST /api/admin/feeds - Create new feed
            if len(path_parts) == 3:
                # Validate required fields
                if not data.get('name') or not data.get('url'):
                    self.send_error_json('Name and URL are required', 400)
                    return

                feed_data = {
                    'name': data['name'],
                    'url': data['url'],
                    'category': data.get('category', 'Uncategorized'),
                    'priority': data.get('priority', 2),
                    'feed_type': data.get('feed_type', 'news'),
                    'description': data.get('description', ''),
                    'is_active': data.get('is_active', True),
                }

                feed = create_feed(feed_data)
                if feed:
                    self.send_json(feed, 201)
                else:
                    self.send_error_json('Failed to create feed', 500)

            # POST /api/admin/feeds/validate - Validate RSS URL
            elif len(path_parts) == 4 and path_parts[3] == 'validate':
                import feedparser
                url = data.get('url')
                if not url:
                    self.send_error_json('URL is required', 400)
                    return

                feed = feedparser.parse(url)
                if feed.bozo and not feed.entries:
                    self.send_json({
                        'valid': False,
                        'error': str(feed.bozo_exception) if hasattr(feed, 'bozo_exception') else 'Invalid feed'
                    })
                else:
                    self.send_json({
                        'valid': True,
                        'title': feed.feed.get('title', 'Unknown'),
                        'description': feed.feed.get('description', ''),
                        'entry_count': len(feed.entries),
                        'sample_entry': feed.entries[0].get('title', '') if feed.entries else None
                    })

            # POST /api/admin/feeds/bulk - Bulk import feeds
            elif len(path_parts) == 4 and path_parts[3] == 'bulk':
                feeds_data = data.get('feeds', [])
                if not feeds_data:
                    self.send_error_json('No feeds provided', 400)
                    return

                created = []
                errors = []
                for feed_item in feeds_data:
                    try:
                        feed = create_feed({
                            'name': feed_item['name'],
                            'url': feed_item['url'],
                            'category': feed_item.get('category', 'Uncategorized'),
                            'priority': feed_item.get('priority', 2),
                            'feed_type': feed_item.get('feed_type', 'news'),
                            'is_active': feed_item.get('is_active', True),
                        })
                        if feed:
                            created.append(feed)
                    except Exception as e:
                        errors.append({'feed': feed_item.get('name', 'Unknown'), 'error': str(e)})

                self.send_json({
                    'created': len(created),
                    'errors': errors,
                    'feeds': created
                })

            else:
                self.send_error_json('Invalid path', 400)

        except json.JSONDecodeError:
            self.send_error_json('Invalid JSON', 400)
        except Exception as e:
            self.send_error_json(str(e), 500)

    def do_PUT(self):
        if not verify_admin_token(self.headers):
            self.send_error_json('Unauthorized', 401)
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            parsed = urlparse(self.path)
            path_parts = parsed.path.strip('/').split('/')

            # PUT /api/admin/feeds/:id - Update feed
            if len(path_parts) == 4:
                feed_id = path_parts[3]

                # Build update data (only include provided fields)
                update_data = {}
                for field in ['name', 'url', 'category', 'priority', 'feed_type', 'description', 'is_active']:
                    if field in data:
                        update_data[field] = data[field]

                if not update_data:
                    self.send_error_json('No fields to update', 400)
                    return

                feed = update_feed(feed_id, update_data)
                if feed:
                    self.send_json(feed)
                else:
                    self.send_error_json('Feed not found', 404)

            # PUT /api/admin/feeds/:id/toggle - Toggle active status
            elif len(path_parts) == 5 and path_parts[4] == 'toggle':
                feed_id = path_parts[3]
                is_active = data.get('is_active', True)
                feed = toggle_feed_active(feed_id, is_active)
                if feed:
                    self.send_json(feed)
                else:
                    self.send_error_json('Feed not found', 404)

            else:
                self.send_error_json('Invalid path', 400)

        except json.JSONDecodeError:
            self.send_error_json('Invalid JSON', 400)
        except Exception as e:
            self.send_error_json(str(e), 500)

    def do_DELETE(self):
        if not verify_admin_token(self.headers):
            self.send_error_json('Unauthorized', 401)
            return

        try:
            parsed = urlparse(self.path)
            path_parts = parsed.path.strip('/').split('/')

            # DELETE /api/admin/feeds/:id - Delete feed
            if len(path_parts) == 4:
                feed_id = path_parts[3]
                result = delete_feed(feed_id)
                self.send_json({'deleted': True, 'id': feed_id})
            else:
                self.send_error_json('Invalid path', 400)

        except Exception as e:
            self.send_error_json(str(e), 500)
