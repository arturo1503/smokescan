import json
from http.server import BaseHTTPRequestHandler

R1_QUESTIONS = [
    {"id": 0, "q": "¿Qué problema específico estás resolviendo y para quién?", "hint": "Describe el dolor puntual y el segmento exacto."},
    {"id": 1, "q": "¿Cómo lo resuelves hoy sin tecnología y cómo lo harás con ella?", "hint": "¿Es una Analgesia (necesidad) o Vitamina (deseo)?"},
    {"id": 2, "q": "¿Por qué ahora? ¿Qué ha cambiado en el mercado?", "hint": "Busca la ventana de oportunidad o cambio regulatorio/tech."},
    {"id": 3, "q": "¿Cuál es tu 'ventaja injusta' o barrera de entrada?", "hint": "IP, red de contactos, data exclusiva o velocidad."},
    {"id": 4, "q": "¿Cómo vas a capturar valor (modelo de negocio)?", "hint": "Quién paga, cuánto y cada cuánto."},
    {"id": 5, "q": "¿Qué recursos humanos y técnicos necesitas para el MVP?", "hint": "Factibilidad inmediata y equipo mínimo viable."},
    {"id": 6, "q": "¿Qué señales de humo o validación tienes hoy?", "hint": "Ventas, LOIs, lista de espera o entrevistas profundas."}
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(R1_QUESTIONS).encode())
