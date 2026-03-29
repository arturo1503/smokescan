# SmokeScan — AI Idea Validator

Validate your startup idea with AI using the **7+7 Method™**. Get a VC-grade diagnostic in minutes.

## 🚀 Deploy to Vercel

1. Fork or import this repo in [vercel.com/new](https://vercel.com/new)
2. Add environment variable: `GEMINI_API_KEY` = your Google Gemini API key
3. Deploy — done!

## 🛠 Local Development

```bash
# Clone
git clone https://github.com/arturo1503/smokescan.git
cd smokescan

# Create .env
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Install dependencies
pip install -r requirements.txt

# Run with Flask (local only)
python app_local.py
```

## 📁 Project Structure

```
api/                  # Vercel Serverless Functions (Python)
  questions_r1.py     # GET  /api/questions/r1
  analyze_r1.py       # POST /api/analyze_r1
  validate.py         # POST /api/validate
public/               # Static frontend (served by Vercel CDN)
  index.html
  style.css
  app.js
vercel.json           # Vercel routing config
requirements.txt      # Python dependencies
```

## 💡 Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS with glassmorphism UI
- **Backend**: Python serverless functions on Vercel
- **AI**: Google Gemini API
- **Search**: DuckDuckGo for market data
- **Validation**: Pydantic models with weighted rubric scoring

## 📝 License

MIT
