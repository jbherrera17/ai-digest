"""Admin API endpoints for feed discovery."""

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.supabase import get_feed_suggestions, search_feed_suggestions, create_feed


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


# Curated feed recommendations organized by niche/industry
NICHE_RECOMMENDATIONS = {
    'coaching': {
        'description': 'Feeds relevant for coaches and consultants',
        'tags': ['business', 'marketing', 'growth', 'leadership'],
        'specific_feeds': [
            {
                'name': 'Seth Godin',
                'url': 'https://seths.blog/feed/',
                'description': 'Marketing and business wisdom',
                'category': 'Newsletter',
            },
            {
                'name': 'First Round Review',
                'url': 'https://review.firstround.com/feed.xml',
                'description': 'Operator insights for growing businesses',
                'category': 'Newsletter',
            },
            {
                'name': 'Lenny\'s Newsletter',
                'url': 'https://www.lennysnewsletter.com/feed',
                'description': 'Product, growth, and career advice',
                'category': 'Substack',
            },
        ],
    },
    'healthcare': {
        'description': 'Feeds relevant for healthcare practices',
        'tags': ['healthcare', 'healthtech', 'compliance'],
        'specific_feeds': [
            {
                'name': 'Healthcare IT News',
                'url': 'https://www.healthcareitnews.com/feed',
                'description': 'Healthcare technology news',
                'category': 'Tech News',
            },
            {
                'name': 'HIPAA Journal',
                'url': 'https://www.hipaajournal.com/feed/',
                'description': 'HIPAA compliance updates',
                'category': 'Newsletter',
            },
        ],
    },
    'manufacturing': {
        'description': 'Feeds relevant for manufacturing businesses',
        'tags': ['manufacturing', 'operations', 'industry'],
        'specific_feeds': [
            {
                'name': 'IndustryWeek',
                'url': 'https://www.industryweek.com/rss.xml',
                'description': 'Manufacturing and operations news',
                'category': 'Tech News',
            },
            {
                'name': 'Manufacturing.net',
                'url': 'https://www.manufacturing.net/rss',
                'description': 'Manufacturing industry insights',
                'category': 'Tech News',
            },
        ],
    },
    'legal': {
        'description': 'Feeds relevant for law firms',
        'tags': ['legal', 'law', 'compliance'],
        'specific_feeds': [
            {
                'name': 'Above the Law',
                'url': 'https://abovethelaw.com/feed/',
                'description': 'Legal industry news and tech',
                'category': 'Tech News',
            },
            {
                'name': 'Artificial Lawyer',
                'url': 'https://www.artificiallawyer.com/feed/',
                'description': 'AI and legal tech coverage',
                'category': 'Newsletter',
            },
        ],
    },
    'professional_services': {
        'description': 'Feeds for accounting, consulting, and professional services',
        'tags': ['accounting', 'finance', 'consulting'],
        'specific_feeds': [
            {
                'name': 'Accounting Today',
                'url': 'https://www.accountingtoday.com/feed',
                'description': 'Accounting and finance tech',
                'category': 'Tech News',
            },
            {
                'name': 'Journal of Accountancy',
                'url': 'https://www.journalofaccountancy.com/rss.xml',
                'description': 'Professional accounting news',
                'category': 'Newsletter',
            },
        ],
    },
    'marketing': {
        'description': 'Feeds for marketing agencies and professionals',
        'tags': ['marketing', 'growth', 'content'],
        'specific_feeds': [
            {
                'name': 'Marketing Examples',
                'url': 'https://marketingexamples.com/feed.xml',
                'description': 'Real-world marketing case studies',
                'category': 'Newsletter',
            },
            {
                'name': 'SparkToro Blog',
                'url': 'https://sparktoro.com/blog/feed/',
                'description': 'Audience research and marketing',
                'category': 'Newsletter',
            },
        ],
    },
    'saas': {
        'description': 'Feeds for SaaS founders and teams',
        'tags': ['saas', 'startups', 'product'],
        'specific_feeds': [
            {
                'name': 'SaaStr',
                'url': 'https://www.saastr.com/feed/',
                'description': 'SaaS growth and operations',
                'category': 'Newsletter',
            },
            {
                'name': 'The Bootstrapped Founder',
                'url': 'https://thebootstrappedfounder.com/feed/',
                'description': 'Building SaaS without VC',
                'category': 'Substack',
            },
            {
                'name': 'Indie Hackers',
                'url': 'https://www.indiehackers.com/feed.xml',
                'description': 'Stories from bootstrapped founders',
                'category': 'Newsletter',
            },
        ],
    },
    'general_ai': {
        'description': 'General AI and tech feeds for any business',
        'tags': ['ai', 'tech', 'business'],
        'specific_feeds': [
            {
                'name': 'Hacker News',
                'url': 'https://hnrss.org/frontpage',
                'description': 'Top tech stories daily',
                'category': 'Tech News',
            },
            {
                'name': 'Product Hunt',
                'url': 'https://www.producthunt.com/feed',
                'description': 'New products and tools',
                'category': 'Tech News',
            },
            {
                'name': 'a16z',
                'url': 'https://a16z.com/feed/',
                'description': 'Tech and AI insights from a16z',
                'category': 'Newsletter',
            },
        ],
    },
}


class handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_json(self, message, status=400):
        self.send_json({'error': message}, status)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        if not verify_admin_token(self.headers):
            self.send_error_json('Unauthorized', 401)
            return

        try:
            parsed = urlparse(self.path)
            path_parts = parsed.path.strip('/').split('/')
            query_params = parse_qs(parsed.query)

            # GET /api/admin/discover - Get discovery options
            if len(path_parts) == 3:
                niches = [
                    {'id': k, 'name': k.replace('_', ' ').title(), 'description': v['description']}
                    for k, v in NICHE_RECOMMENDATIONS.items()
                ]
                self.send_json({
                    'niches': niches,
                    'available_tags': ['ai', 'tech', 'business', 'marketing', 'healthcare', 'legal', 'manufacturing', 'saas', 'growth'],
                })

            # GET /api/admin/discover/niche/:niche - Get recommendations for a niche
            elif len(path_parts) == 5 and path_parts[3] == 'niche':
                niche = path_parts[4]
                if niche not in NICHE_RECOMMENDATIONS:
                    self.send_error_json(f'Unknown niche: {niche}', 404)
                    return

                niche_data = NICHE_RECOMMENDATIONS[niche]

                # Get from database if available
                try:
                    db_suggestions = get_feed_suggestions(tags=niche_data['tags'], limit=10)
                except Exception:
                    db_suggestions = []

                # Combine with hardcoded recommendations
                all_suggestions = niche_data['specific_feeds'] + [
                    {
                        'name': s['name'],
                        'url': s['url'],
                        'description': s.get('description', ''),
                        'category': s.get('category', 'Newsletter'),
                        'from_database': True,
                    }
                    for s in db_suggestions
                ]

                # Deduplicate by URL
                seen_urls = set()
                unique_suggestions = []
                for s in all_suggestions:
                    if s['url'] not in seen_urls:
                        seen_urls.add(s['url'])
                        unique_suggestions.append(s)

                self.send_json({
                    'niche': niche,
                    'description': niche_data['description'],
                    'suggestions': unique_suggestions[:15],
                    'count': len(unique_suggestions),
                })

            # GET /api/admin/discover/search?q=term - Search suggestions
            elif len(path_parts) == 4 and path_parts[3] == 'search':
                search_term = query_params.get('q', [''])[0]
                if not search_term:
                    self.send_error_json('Search term (q) is required', 400)
                    return

                try:
                    results = search_feed_suggestions(search_term, limit=20)
                except Exception:
                    results = []

                # Also search hardcoded recommendations
                search_lower = search_term.lower()
                hardcoded_matches = []
                for niche_data in NICHE_RECOMMENDATIONS.values():
                    for feed in niche_data['specific_feeds']:
                        if search_lower in feed['name'].lower() or search_lower in feed.get('description', '').lower():
                            hardcoded_matches.append(feed)

                all_results = results + hardcoded_matches

                # Deduplicate
                seen_urls = set()
                unique_results = []
                for r in all_results:
                    if r['url'] not in seen_urls:
                        seen_urls.add(r['url'])
                        unique_results.append(r)

                self.send_json({
                    'query': search_term,
                    'results': unique_results[:20],
                    'count': len(unique_results),
                })

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

            # POST /api/admin/discover/add - Add selected suggestions to feeds
            if len(path_parts) == 4 and path_parts[3] == 'add':
                feeds_to_add = data.get('feeds', [])
                if not feeds_to_add:
                    self.send_error_json('No feeds provided', 400)
                    return

                added = []
                errors = []

                for feed in feeds_to_add:
                    try:
                        created = create_feed({
                            'name': feed['name'],
                            'url': feed['url'],
                            'category': feed.get('category', 'Newsletter'),
                            'priority': feed.get('priority', 2),
                            'feed_type': feed.get('feed_type', 'newsletter'),
                            'description': feed.get('description', ''),
                            'is_active': True,
                        })
                        if created:
                            added.append(created)
                    except Exception as e:
                        errors.append({
                            'feed': feed.get('name', 'Unknown'),
                            'error': str(e),
                        })

                self.send_json({
                    'added': len(added),
                    'feeds': added,
                    'errors': errors,
                })

            else:
                self.send_error_json('Invalid path', 400)

        except json.JSONDecodeError:
            self.send_error_json('Invalid JSON', 400)
        except Exception as e:
            self.send_error_json(str(e), 500)
