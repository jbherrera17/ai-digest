"""POST /api/export - Export digest as markdown.

Request body: { "top_stories": [...], "smb_spotlight": [...], "all_articles": [...] }
Response: markdown text file download
"""

import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        top_stories = body.get('top_stories', [])
        smb_spotlight = body.get('smb_spotlight', [])
        articles = body.get('all_articles', [])

        md = []
        md.append("# AI News Digest")
        md.append(f"\n*Generated: {datetime.now().strftime('%B %d, %Y')}*\n")

        md.append("\n## Top Stories\n")
        for i, article in enumerate(top_stories, 1):
            md.append(f"### {i}. {article['title']}")
            md.append(f"*{article['source']} | {article['published_display']}*\n")
            md.append(f"{article['summary']}\n")
            md.append(f"[Read more]({article['link']})\n")

        if smb_spotlight:
            md.append("\n## SMB AI Spotlight\n")
            for article in smb_spotlight:
                md.append(f"### {article['title']}")
                md.append(f"*{article['source']} | SMB Score: {article['smb_score']}/10*\n")
                md.append(f"{article['summary']}\n")
                md.append(f"[Read more]({article['link']})\n")

        md.append("\n## Quick Hits\n")
        for article in articles[:10]:
            md.append(f"- **{article['title']}** - {article['source']} ([link]({article['link']}))")

        content = "\n".join(md)

        self.send_response(200)
        self.send_header('Content-Type', 'text/markdown')
        self.send_header('Content-Disposition', 'attachment; filename=ai_digest.md')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content.encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
