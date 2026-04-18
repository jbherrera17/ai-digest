"""Admin API endpoints for skills registry management."""

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.supabase import (
    upsert_skill_sources, upsert_skills, upsert_skill_matches,
    update_match_review, create_skill_adoption,
    get_skill_sources, get_all_skills
)


def verify_admin_token(headers):
    """Verify admin authentication token."""
    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header[7:]
    admin_token = os.environ.get('ADMIN_API_TOKEN', '')
    if not admin_token:
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

            # POST /api/admin/skills/sync - Sync full registry JSON
            if len(path_parts) == 4 and path_parts[3] == 'sync':
                return self._handle_sync(data)

            # POST /api/admin/skills/adopt - Adopt an expert skill
            elif len(path_parts) == 4 and path_parts[3] == 'adopt':
                if not data.get('expert_skill_id'):
                    self.send_error_json('expert_skill_id is required', 400)
                    return
                adoption = create_skill_adoption(data)
                if adoption:
                    self.send_json(adoption, 201)
                else:
                    self.send_error_json('Failed to create adoption', 500)

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

            # PUT /api/admin/skills/matches/:id - Update match review
            if len(path_parts) == 5 and path_parts[3] == 'matches':
                match_id = path_parts[4]
                if not data.get('review_status'):
                    self.send_error_json('review_status is required', 400)
                    return
                if data['review_status'] not in ('pending', 'approved', 'rejected', 'override'):
                    self.send_error_json('Invalid review_status', 400)
                    return

                result = update_match_review(match_id, data)
                if result:
                    self.send_json(result)
                else:
                    self.send_error_json('Match not found', 404)
            else:
                self.send_error_json('Invalid path', 400)

        except json.JSONDecodeError:
            self.send_error_json('Invalid JSON', 400)
        except Exception as e:
            self.send_error_json(str(e), 500)

    def _handle_sync(self, data):
        """Handle full registry JSON sync."""
        if not data.get('sources') or not data.get('skills'):
            self.send_error_json('Registry JSON must contain sources and skills', 400)
            return

        # Step 1: Upsert sources
        sources_synced = upsert_skill_sources(data['sources'])

        # Step 2: Build source_key -> UUID map
        db_sources = get_skill_sources()
        source_map = {s['source_key']: s['id'] for s in db_sources}

        # Step 3: Upsert skills
        skills_synced = upsert_skills(data['skills'], source_map)

        # Step 4: Build skill_id -> UUID map for matches
        db_skills = get_all_skills()
        skill_id_map = {s['skill_id']: s['id'] for s in db_skills}

        # Step 5: Upsert matches (preserving reviewed ones)
        matches_synced = 0
        if data.get('matchResults'):
            matches_synced = upsert_skill_matches(data['matchResults'], skill_id_map)

        self.send_json({
            'sources_synced': sources_synced,
            'skills_synced': skills_synced,
            'matches_synced': matches_synced,
        })
