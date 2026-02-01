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
            viral = article.get('viral_score', 0) >= 4
            md.append(f"### {i}. {article['title']}" + (" [TRENDING]" if viral else ""))
            md.append(f"*{article['source']} | {article['published_display']}*\n")

            bullets = article.get('key_bullets', [])
            if bullets:
                md.append("**Key Points:**")
                for b in bullets:
                    md.append(f"- {b}")
                md.append("")
            else:
                md.append(f"{article['summary']}\n")

            impact = article.get('impact')
            if impact:
                md.append("#### What it Means\n")
                md.append(f"**General Impact:** {impact['general_impact']}\n")
                md.append(f"**Impact to SMBs:** {impact['smb_impact']}\n")

            suggestions = article.get('content_suggestions')
            if suggestions:
                md.append("**Content Ideas (Trending Topic):**")
                for s in suggestions:
                    md.append(f"- {s}")
                md.append("")

            md.append(f"[Read more]({article['link']})\n")

        if smb_spotlight:
            md.append("\n## SMB AI Spotlight\n")
            for article in smb_spotlight:
                md.append(f"### {article['title']}")
                md.append(f"*{article['source']} | SMB Score: {article['smb_score']}/10*\n")

                bullets = article.get('key_bullets', [])
                if bullets:
                    for b in bullets:
                        md.append(f"- {b}")
                    md.append("")
                else:
                    md.append(f"{article['summary']}\n")

                impact = article.get('impact')
                if impact:
                    md.append(f"**General Impact:** {impact['general_impact']}\n")
                    md.append(f"**Impact to SMBs:** {impact['smb_impact']}\n")

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
