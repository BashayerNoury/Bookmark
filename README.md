# Bookmark

ChatGPT-style **AI book recommendation chatbot** — Django REST + React (Vite), **Inter** UI font.

Recommendations are grounded in Bookmark’s catalog. When configured, **Google Gemini** (free tier) writes the conversational reply and picks the best matches.

## Cost

| What | Cost |
|------|------|
| Running locally | Free |
| **Google Gemini** (recommended) | Free tier via [Google AI Studio](https://aistudio.google.com/apikey) |
| Hosting later | Whatever host you choose |

Without `GEMINI_API_KEY`, chat still works using local catalog matching.

## Quick start

```bash
# Backend
cd /Users/bash/Projects/Bookmark
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Put your free Gemini key in .env:
# GEMINI_API_KEY=your_key_here
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

## Gemini setup

1. Open https://aistudio.google.com/apikey  
2. Create an API key  
3. Add to `.env`:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

4. Restart `runserver`

## Chat API

`POST /api/chat/` with `{ "message", "history", "limit" }` → `{ "reply", "books" }`.

Book chips open Goodreads and show Open Library covers.
