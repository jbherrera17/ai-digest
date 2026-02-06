"""Admin API endpoints for ICP profile management."""

import json
import os
import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.supabase import (
    get_all_icp_profiles, get_icp_profile_by_id, create_icp_profile,
    update_icp_profile, delete_icp_profile, set_default_icp_profile
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


def parse_icp_from_text(text: str) -> dict:
    """
    Parse plain text ICP description into structured JSON format.

    Attempts to extract:
    - Business type / audience
    - Pain points
    - Keywords
    - Goals/desires

    Returns a structured ICP data object.
    """
    text_lower = text.lower()
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Initialize structure
    icp_data = {
        'parsed_from_text': True,
        'raw_text': text,
        'audience_overview': {
            'one_sentence_summary': '',
            'primary_identity': '',
        },
        'pain_points': {
            'top_pains': [],
        },
        'language_patterns': {
            'keywords_used': [],
        },
        'desired_transformation': {
            'outcomes': [],
        },
    }

    # Extract business type (look for patterns like "I am a...", "We are...", "targeting...")
    identity_patterns = [
        r"(?:i am|we are|i'm|we're)\s+(?:a\s+)?([^.!?\n]+)",
        r"(?:targeting|serve|help|work with)\s+([^.!?\n]+)",
        r"(?:my|our)\s+(?:clients|customers|audience)\s+(?:are|include)\s+([^.!?\n]+)",
    ]
    for pattern in identity_patterns:
        match = re.search(pattern, text_lower)
        if match:
            icp_data['audience_overview']['primary_identity'] = match.group(1).strip().title()
            break

    # Extract pain points (look for keywords)
    pain_indicators = ['struggle', 'challenge', 'problem', 'issue', 'pain', 'frustrated', 'difficult', 'hard to', 'need help with']
    for line in lines:
        line_lower = line.lower()
        if any(ind in line_lower for ind in pain_indicators):
            # Clean up the pain point
            pain = re.sub(r'^[-•*]\s*', '', line)  # Remove bullet points
            if len(pain) > 10 and len(pain) < 200:
                icp_data['pain_points']['top_pains'].append(pain)

    # Extract keywords (common business/industry terms)
    keyword_candidates = []
    business_terms = [
        'automation', 'efficiency', 'productivity', 'growth', 'scale', 'revenue',
        'marketing', 'sales', 'leads', 'clients', 'customers', 'operations',
        'workflow', 'process', 'technology', 'digital', 'online', 'content',
        'coaching', 'consulting', 'healthcare', 'manufacturing', 'legal',
        'accounting', 'finance', 'real estate', 'e-commerce', 'saas',
        'ai', 'artificial intelligence', 'machine learning', 'data',
    ]
    for term in business_terms:
        if term in text_lower:
            keyword_candidates.append(term)
    icp_data['language_patterns']['keywords_used'] = list(set(keyword_candidates))[:15]

    # Extract goals (look for "want to", "need to", "goal", etc.)
    goal_patterns = [
        r"(?:want to|need to|looking to|trying to|goal is to)\s+([^.!?\n]+)",
        r"(?:my|our)\s+goal[s]?\s+(?:is|are|include)\s+([^.!?\n]+)",
    ]
    for pattern in goal_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if len(match) > 10 and len(match) < 200:
                icp_data['desired_transformation']['outcomes'].append(match.strip().capitalize())

    # If we couldn't extract structured data, use the whole text as summary
    if not icp_data['audience_overview']['primary_identity'] and lines:
        icp_data['audience_overview']['one_sentence_summary'] = lines[0][:200]

    # Generate a basic summary if we have some data
    if icp_data['audience_overview']['primary_identity']:
        identity = icp_data['audience_overview']['primary_identity']
        pains = icp_data['pain_points']['top_pains'][:2]
        pain_text = f" who struggle with {' and '.join(pains)}" if pains else ""
        icp_data['audience_overview']['one_sentence_summary'] = f"{identity}{pain_text}"

    return icp_data


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

            # GET /api/admin/icps - List all ICP profiles
            if len(path_parts) == 3:
                profiles = get_all_icp_profiles()
                self.send_json({'profiles': profiles, 'count': len(profiles)})

            # GET /api/admin/icps/:id - Get single profile
            elif len(path_parts) == 4:
                profile_id = path_parts[3]
                profile = get_icp_profile_by_id(profile_id)
                if profile:
                    self.send_json(profile)
                else:
                    self.send_error_json('ICP profile not found', 404)
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

            # POST /api/admin/icps - Create new ICP profile
            if len(path_parts) == 3:
                name = data.get('name')
                if not name:
                    self.send_error_json('Name is required', 400)
                    return

                # Handle different input types
                source_type = data.get('source_type', 'json')
                icp_data = None

                if source_type == 'text':
                    # Parse from plain text
                    text = data.get('text', '')
                    if not text:
                        self.send_error_json('Text content is required for text source type', 400)
                        return
                    icp_data = parse_icp_from_text(text)

                elif source_type == 'json':
                    # Use provided JSON data
                    icp_data = data.get('data', {})
                    if not icp_data:
                        self.send_error_json('ICP data is required', 400)
                        return

                else:
                    self.send_error_json(f'Invalid source_type: {source_type}', 400)
                    return

                profile_data = {
                    'name': name,
                    'description': data.get('description', ''),
                    'data': icp_data,
                    'source_type': source_type,
                    'is_active': data.get('is_active', True),
                    'is_default': data.get('is_default', False),
                }

                profile = create_icp_profile(profile_data)
                if profile:
                    self.send_json(profile, 201)
                else:
                    self.send_error_json('Failed to create ICP profile', 500)

            # POST /api/admin/icps/parse - Parse text to preview ICP structure
            elif len(path_parts) == 4 and path_parts[3] == 'parse':
                text = data.get('text', '')
                if not text:
                    self.send_error_json('Text is required', 400)
                    return

                parsed_icp = parse_icp_from_text(text)
                self.send_json({
                    'parsed': True,
                    'data': parsed_icp,
                    'pain_points_found': len(parsed_icp['pain_points']['top_pains']),
                    'keywords_found': len(parsed_icp['language_patterns']['keywords_used']),
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

            # PUT /api/admin/icps/:id - Update profile
            if len(path_parts) == 4:
                profile_id = path_parts[3]

                update_data = {}
                for field in ['name', 'description', 'data', 'is_active', 'is_default']:
                    if field in data:
                        update_data[field] = data[field]

                if not update_data:
                    self.send_error_json('No fields to update', 400)
                    return

                profile = update_icp_profile(profile_id, update_data)
                if profile:
                    self.send_json(profile)
                else:
                    self.send_error_json('ICP profile not found', 404)

            # PUT /api/admin/icps/:id/default - Set as default
            elif len(path_parts) == 5 and path_parts[4] == 'default':
                profile_id = path_parts[3]
                profile = set_default_icp_profile(profile_id)
                if profile:
                    self.send_json(profile)
                else:
                    self.send_error_json('ICP profile not found', 404)

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

            # DELETE /api/admin/icps/:id - Delete profile
            if len(path_parts) == 4:
                profile_id = path_parts[3]
                result = delete_icp_profile(profile_id)
                self.send_json({'deleted': True, 'id': profile_id})
            else:
                self.send_error_json('Invalid path', 400)

        except Exception as e:
            self.send_error_json(str(e), 500)
