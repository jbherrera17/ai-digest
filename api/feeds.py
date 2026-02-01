"""GET /api/feeds - Return list of available RSS feeds."""

import json
from http.server import BaseHTTPRequestHandler
from api.shared import RSS_FEEDS


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(RSS_FEEDS).encode())
