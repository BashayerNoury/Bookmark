# Bookmark

ChatGPT-style **AI book recommendation chatbot** — Django REST + React (Vite), **Inter** UI.

Suggestions come from **Google Gemini** (not a local catalog). Covers/ISBNs via **Open Library**. Cards open on **Goodreads**.

## Cost

| What | Cost |
|------|------|
| Local + Gemini + Open Library | Free |
| **Live hosting (Render free)** | Free (app sleeps after idle; cold start ~30–60s) |

## Quick start (local)

```bash
cd /Users/bash/Projects/Bookmark
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GEMINI_API_KEY=...
python manage.py migrate
python manage.py runserver

cd frontend && npm install && npm run dev
```

## Deploy live for free (Render)

One service serves both the chat UI and API.

1. Push this branch to GitHub (`testing` or `master`)
2. Go to [https://render.com](https://render.com) → **New** → **Blueprint**
3. Connect `BashayerNoury/Bookmark` and use `render.yaml`
4. Set secret env var **`GEMINI_API_KEY`** (from [Google AI Studio](https://aistudio.google.com/apikey))
5. Deploy — you’ll get a URL like `https://bookmark-xxxx.onrender.com`

Or manually: **New Web Service** → this repo →:

- **Build:** `chmod +x build.sh && ./build.sh`
- **Start:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- **Env:** `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com`, `GEMINI_API_KEY=...`, `GEMINI_MODEL=gemini-2.0-flash`

### Free-tier notes

- App **spins down** when idle; first visit after sleep is slow
- SQLite on free hosting is fine for demos (data may reset on redeploy)
- Keep `master` as live if you prefer; deploy from `testing` until ready

## Gemini setup

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

## Chat API

`POST /api/chat/` → `{ "reply", "books" }`
