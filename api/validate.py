import os
import json
import traceback
from http.server import BaseHTTPRequestHandler
from google import genai
from duckduckgo_search import DDGS
from pydantic import BaseModel
from typing import List, Optional

class Rubric(BaseModel):
    market_clarity: int
    tech_feasibility: int
    competition_intensity: int
    mvp_simplicity: int
    regulatory_risk: int
    demand_strength: int

class Scenarios(BaseModel):
    optimistic: str
    neutral: str
    pessimistic: str

class ValidationResponse(BaseModel):
    status: str
    score: Optional[int] = None
    risk: Optional[int] = None
    marketText: Optional[str] = None
    techText: Optional[str] = None
    techStatusText: Optional[str] = None
    competitionText: Optional[str] = None
    stars: Optional[str] = None
    mitigation_advice: Optional[List[str]] = None
    scenarios: Optional[Scenarios] = None
    investment_estimate: Optional[str] = None
    cash_flow_projection: Optional[str] = None
    rubric: Optional[Rubric] = None

def calculate_metrics(rubric: Rubric):
    s = (rubric.market_clarity * 0.20) + (rubric.tech_feasibility * 0.15) + \
        ((10 - rubric.competition_intensity) * 0.15) + (rubric.mvp_simplicity * 0.15) + \
        ((10 - rubric.regulatory_risk) * 0.10) + (rubric.demand_strength * 0.25)
    final_score = min(max(int(s * 10), 0), 100)
    r = ((10 - rubric.market_clarity) * 0.15) + ((10 - rubric.tech_feasibility) * 0.20) + \
        (rubric.competition_intensity * 0.15) + ((10 - rubric.mvp_simplicity) * 0.15) + \
        (rubric.regulatory_risk * 0.15) + ((10 - rubric.demand_strength) * 0.20)
    final_risk = min(max(int(r * 10), 0), 100)
    return final_score, final_risk

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    return genai.Client(api_key=api_key) if api_key else None

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
        project_name = body.get('projectName', 'New Project')
        answers_r1 = body.get('answers_r1', [])
        answers_r2 = body.get('answers_r2', [])

        r1_ctx = "\n".join([f"Q{i+1}: {a}" for i, a in enumerate(answers_r1)])
        r2_ctx = "\n".join([f"R2-Q{x['why_index']+1}: {x['answer']}" for x in answers_r2])

        search_context = ""
        try:
            ddgs = DDGS()
            results = list(ddgs.text(f"market for {project_name}", max_results=2))
            search_context = "\n".join([f"{r['title']}: {r['body']}" for r in results])
        except:
            search_context = "No market data."

        client = get_client()
        if not client:
            self._respond(200, {"status": "error", "message": "No API Key"})
            return

        prompt = f"Evaluate {project_name}. R1: {r1_ctx}. R2: {r2_ctx}. Context: {search_context}. Strict VC evaluation. Output JSON for diagnosis."
        try:
            response = client.models.generate_content(
                model='gemini-flash-latest', contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": ValidationResponse}
            )
            analysis = json.loads(response.text.strip())
            if analysis.get("status") == "success" and "rubric" in analysis:
                rubric_obj = Rubric(**analysis["rubric"])
                score, risk = calculate_metrics(rubric_obj)
                analysis["score"] = score
                analysis["risk"] = risk
            self._respond(200, analysis)
        except Exception as e:
            traceback.print_exc()
            self._respond(500, {"error": str(e)})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
