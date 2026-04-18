"""Public API endpoints for skills registry."""

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.supabase import (
    get_all_skills, get_skill_sources, get_skill_matches,
    get_unmatched_expert_skills, get_skill_stats
)


class handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_json(self, message, status=400):
        self.send_json({'error': message}, status)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path_parts = parsed.path.strip('/').split('/')
            params = parse_qs(parsed.query)

            # GET /api/skills - List all skills
            if len(path_parts) == 2:
                filters = {}
                if params.get('department'):
                    filters['department'] = params['department'][0]
                if params.get('type'):
                    filters['type'] = params['type'][0]
                if params.get('source'):
                    filters['source'] = params['source'][0]
                if params.get('search'):
                    filters['search'] = params['search'][0]

                skills = get_all_skills(filters if filters else None)
                self.send_json({'skills': skills, 'count': len(skills)})

            # GET /api/skills/stats
            elif len(path_parts) == 3 and path_parts[2] == 'stats':
                stats = get_skill_stats()
                self.send_json(stats)

            # GET /api/skills/matches
            elif len(path_parts) == 3 and path_parts[2] == 'matches':
                status_filter = params.get('status', [None])[0]
                matches = get_skill_matches(status_filter)
                self.send_json({'matches': matches, 'count': len(matches)})

            # GET /api/skills/suggestions
            elif len(path_parts) == 3 and path_parts[2] == 'suggestions':
                suggestions = get_unmatched_expert_skills()
                self.send_json({'suggestions': suggestions, 'count': len(suggestions)})

            # GET /api/skills/sources
            elif len(path_parts) == 3 and path_parts[2] == 'sources':
                sources = get_skill_sources()
                self.send_json({'sources': sources, 'count': len(sources)})

            else:
                self.send_error_json('Invalid path', 400)

        except Exception as e:
            self.send_error_json(str(e), 500)
