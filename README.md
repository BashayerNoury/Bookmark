# Bookmark

ChatGPT-style **AI book recommendation chatbot** — Django REST backend + React chat UI.

You open the app and talk to Bookmark. It recommends books from its catalog based on mood, vibe, and what you ask for.

## Quick start

### Backend

```bash
cd /Users/bash/Projects/Bookmark
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_books
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173) — chat only.

## Chat API

`POST /api/chat/`

```json
{
  "message": "cozy fantasy with found family",
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "limit": 4
}
```

Returns `{ "reply": "...", "books": [...] }`.

Optional: set `OPENAI_API_KEY` in `.env` for richer recommendation blurbs.
