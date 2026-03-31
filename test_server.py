import http.server
import socketserver
import json
import os

PORT = 3000
DIRECTORY = "public"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/api/questions/r1':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = [{"q": "¿Cuál es tu modelo de negocio?", "id": 1}]
            self.wfile.write(json.dumps(data).encode())
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/analyze_r1':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = {"followups": []}
            self.wfile.write(json.dumps(data).encode())
            return
        if self.path == '/api/validate':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = {
                "score": 85,
                "risk": 15,
                "marketText": "High Growth",
                "stars": "⭐⭐⭐⭐",
                "techText": "Feasible",
                "techStatusText": "Good",
                "competitionText": "Moderate",
                "mitigation_advice": ["Do better"],
                "scenarios": {
                    "optimistic": "Much money",
                    "neutral": "Some money",
                    "pessimistic": "No money"
                },
                "investment_estimate": "$100k",
                "cash_flow_projection": "Positive in 6mo",
                "rubric": {"market_clarity": 8, "tech_feasibility": 9}
            }
            self.wfile.write(json.dumps(data).encode())
            return

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
