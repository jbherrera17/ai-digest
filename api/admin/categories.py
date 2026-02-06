"""Admin API endpoints for category management."""

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.supabase import (
    get_all_categories, create_category,
    update_category, delete_category
)


def verify_admin_token(headers):
    """Verify admin authentication token."""
    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header[7:]
    admin_token = os.environ.get('ADMIN_API_TOKEN', '')
    if not admin_token:
        return True  # Dev mode
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
            categories = get_all_categories()
            self.send_json({'categories': categories, 'count': len(categories)})
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

            name = data.get('name')
            if not name:
                self.send_error_json('Name is required', 400)
                return

            category_data = {
                'name': name,
                'display_order': data.get('display_order', 0),
                'color': data.get('color', '#6366f1'),
            }

            category = create_category(category_data)
            if category:
                self.send_json(category, 201)
            else:
                self.send_error_json('Failed to create category', 500)

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

            if len(path_parts) == 4:
                category_id = path_parts[3]

                update_data = {}
                for field in ['name', 'display_order', 'color']:
                    if field in data:
                        update_data[field] = data[field]

                if not update_data:
                    self.send_error_json('No fields to update', 400)
                    return

                category = update_category(category_id, update_data)
                if category:
                    self.send_json(category)
                else:
                    self.send_error_json('Category not found', 404)
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

            if len(path_parts) == 4:
                category_id = path_parts[3]
                result = delete_category(category_id)
                self.send_json({'deleted': True, 'id': category_id})
            else:
                self.send_error_json('Invalid path', 400)

        except Exception as e:
            self.send_error_json(str(e), 500)
