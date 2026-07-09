# ALTREON Backend — AI-Powered Cybersecurity Incident Triage

## Quick Start

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env file and fill in your API keys
copy .env.example .env

# 5. Run the server
python run.py
```

Server starts at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

## API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| POST | `/report` | Submit a new incident report |
| POST | `/webhook/auto` | Webhook for auto alerts (EDR/Firewall/AV) |
| POST | `/employee/chat` | AI-guided chat for employee reporting |
| POST | `/ai/process` | Run AI correlation & severity engine |
| POST | `/route` | Apply Cybersec routing & final reporting |
| GET | `/incident/{id}` | Get full incident details |
| GET | `/reports/employee/{name}` | Reports by employee |
| GET | `/reports/cybersec/pending` | Incidents awaiting routing |
| GET | `/reports/admin/all` | Master list for admin dashboard |

## Environment Variables

See `.env.example` for the full list. Required:
- `ACTIVE_AI_PROVIDER` — AI provider (e.g. `"groq"`, `"google"`, `"openai"`)
- `GROQ_API_KEY` / `GEMINI_API_KEY` / `OPENAI_API_KEY` — AI provider key
- `TWILIO_*` — For SMS escalation (optional)

## Tech Stack

- **Python** / **FastAPI**
- **SQLite** + **SQLAlchemy**
- **Open-source LLMs** — DeepSeek V4, GLM-4, MiniMax (any OpenAI-compatible API)
- **Twilio** (SMS alerts)
