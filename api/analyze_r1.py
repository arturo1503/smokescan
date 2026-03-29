import os
import json
import traceback
from http.server import BaseHTTPRequestHandler
from google import genai
from pydantic import BaseModel
from typing import List

class FollowUp(BaseModel):
    why_index: int
    pregunta: str
    razon: str

class FollowUpResponse(BaseModel):
    followups: List[FollowUp]

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))
        answers = body.get('answers', [])

        client = get_client()
        if not client:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"followups": [{"why_index": 0, "pregunta": "Mock Follow-up Q1", "razon": "superficial"}]}).encode())
            return

        prompt = f"Analyze these 7 responses: {json.dumps(answers)}. Generate up to 7 drill-down follow-up questions for superficial or weak answers. Output JSON with 'followups' list of {{why_index, pregunta, razon}}."

        try:
            response = client.models.generate_content(
                model='gemini-flash-latest', contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": FollowUpResponse}
            )
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.text.encode())
        except Exception as e:
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
