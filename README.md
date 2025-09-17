 LiveKit Memory Chat

## What this does
A full local dev setup that runs:
- LiveKit server (dev mode)
- Backend agent (receives LiveKit chat messages, uses mem0 for memory, calls Gemini for replies)
- Token server (FastAPI) to generate LiveKit tokens
- Frontend (Next.js) chat UI to send/receive text

## Quick local run (without Docker)
1. Backend:
   cd backend
   python -m venv .venv
   .\\.venv\\Scripts\\activate
   pip install -r requirements.txt
   copy .env.example .env
   :: Edit backend\\.env and set GEMINI_API_KEY and MEM0_API_KEY
   python token_server.py   # runs at http://localhost:8000
   python agent.py

2. Frontend:
   cd frontend
   npm install
   npm run dev
   Open http://localhost:3000
   Paste LIVEKIT URL (e.g. ws://localhost:7880) and Token server URL (e.g. http://localhost:8000/token)

## Using Docker (one command)
Set GEMINI_API_KEY and MEM0_API_KEY in your shell, then:
docker-compose up --build

Frontend: http://localhost:3000
Token server: http://localhost:8000/token?identity=alice
LiveKit (dev): ws://localhost:7880