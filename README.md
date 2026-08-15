# Bookmark

ChatGPT-style **AI book recommendation chatbot** — Django REST + React (Vite).

Recommendations use local catalog matching (not required LLM). Optional `OPENAI_API_KEY` only enriches reply blurbs.

## Cost

| What | Cost |
|------|------|
| Running locally | Free |
| OpenAI explanations (optional) | Only if you set `OPENAI_API_KEY` — billed by OpenAI |
| Hosting later | Whatever host you choose |

## Quick start

```bash
# Backend
cd /Users/bash/Projects/Bookmark
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_books
python manage.py runserver

# Frontend
cd frontend
npm install
npm run dev
```

- App: http://127.0.0.1:5173  
- API: http://127.0.0.1:8000/api/

## Chat API

`POST /api/chat/` with `{ "message", "history", "limit" }` → `{ "reply", "books" }`.

Book chips open Goodreads and show cover images from Open Library.
