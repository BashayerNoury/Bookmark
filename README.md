# Bookmark

**Bookmark** is an AI book-recommendation chatbot — chat like ChatGPT or Claude, get real book picks, open them on Goodreads.

Built by **Bashayer** as a product-minded full-stack experiment: one simple chat surface, strong branding, and free-tier AI so anyone can try personalized reading suggestions without a paid catalog or paid LLM lock-in.

---

## Story

Most book apps bury recommendations behind feeds, shelves, and filters. Bookmark flips that:

1. You say what you’re in the mood for (“cozy fantasy,” “dark thriller,” “books like *Project Hail Mary*”).
2. **Google Gemini** suggests real published books in a natural conversation.
3. **Open Library** enriches each pick with cover art and ISBN.
4. Each card opens on **Goodreads** so you can save, rate, or buy.

No local fake catalog for chat. The AI talks to the real book world; the UI stays calm, minimal, and on-brand.

---

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| **Frontend** | React 19 + Vite | Fast chat UI, Inter font |
| **Routing / state** | Single-page chat (`App.jsx`) | ChatGPT-like, no extra pages |
| **HTTP** | Axios | API client |
| **Backend** | Django 6 + Django REST Framework | Solid API + admin |
| **Auth (optional)** | SimpleJWT | Ready for accounts later |
| **AI** | Google Gemini (`gemini-3.1-flash-lite`) | Free-tier conversational recs |
| **Covers / ISBN** | Open Library API | Free metadata |
| **Outbound links** | Goodreads search | Familiar reader destination |
| **DB (dev / free host)** | SQLite | Zero setup |
| **Prod server** | Gunicorn + WhiteNoise | One service serves API + built React |
| **Hosting** | Render (free tier) | Blueprint via `render.yaml` |

```text
Browser (React chat)
    │  POST /api/chat/
    ▼
Django API
    ├── Gemini  → titles + conversational reply
    └── Open Library → cover_url, isbn, subjects
    ▼
Book chips → Goodreads
```

---

## Brand & colors

Notion-inspired neutrals, **maroon** instead of Notion blue. **Inter** for a modern UI. Light and dark modes.

### Light

| Token | Hex | Use |
|-------|-----|-----|
| Background | `#ffffff` | App canvas |
| Panel | `#f7f6f3` | Sidebar |
| Ink | `#37352f` | Primary text |
| Muted | `#787774` | Secondary text |
| Line | `#e9e9e7` | Borders |
| Accent (maroon) | `#800020` | Brand, send, selection, covers fallback |
| Accent hover | `#5c0018` | Pressed / hover |
| Accent soft | `#f5e8ec` | Soft highlight |
| User bubble | `#f1f1ef` | User messages |

### Dark

| Token | Hex | Use |
|-------|-----|-----|
| Background | `#212121` | App canvas |
| Panel | `#171717` | Sidebar |
| Ink | `#ececec` | Primary text |
| Muted | `#9b9a97` | Secondary text |
| Line | `#2f2f2f` | Borders |
| Accent | `#a33a52` | Brand (softer maroon) |
| Accent hover | `#c24b65` | Hover |
| User bubble | `#2f2f2f` | User messages |

Text selection uses the accent maroon. CSS variables live in [`frontend/src/index.css`](frontend/src/index.css).

---

## Features

- ChatGPT / Claude–style chat (sidebar, starters, composer, light/dark)
- Gemini-powered recommendations (no local suggestion catalog)
- Open Library covers + ISBN enrichment
- Goodreads links on every book chip
- Django admin at `/admin/` (optional)
- Free Render deploy (UI + API in one service)

---

## Branches

| Branch | Purpose |
|--------|---------|
| **`master`** | Live / stable |
| **`stage`** | Staging & experiments (current) |

Repo: [github.com/BashayerNoury/Bookmark](https://github.com/BashayerNoury/Bookmark)

---

## Cost

| Piece | Cost |
|-------|------|
| Local run | Free |
| Gemini | Free tier ([AI Studio](https://aistudio.google.com/apikey)) |
| Open Library | Free |
| Render hosting | Free (sleeps when idle; cold start ~30–60s) |

---

## What you need

1. **Python 3.12+** and a venv  
2. **Node 20+** / npm  
3. **Gemini API key** — https://aistudio.google.com/apikey  
4. (Optional) **Render** account for live hosting  
5. (Optional) GitHub access to this repo  

---

## Local setup

```bash
# Clone
git clone https://github.com/BashayerNoury/Bookmark.git
cd Bookmark
git checkout stage

# Backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=...

python manage.py migrate
python manage.py runserver

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

| Service | URL |
|---------|-----|
| Chat UI | http://127.0.0.1:5173 |
| API | http://127.0.0.1:8000/api/ |
| Admin | http://127.0.0.1:8000/admin/ |

Create an admin user if needed:

```bash
python manage.py createsuperuser
```

### `.env`

```env
SECRET_KEY=change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

Without `GEMINI_API_KEY`, chat will ask you to add one (it will not invent picks from a local catalog).

---

## Deploy live (Render — free)

One service serves the built React app and the Django API.

1. Push `stage` (or merge to `master`) on GitHub  
2. [Render](https://render.com) → **New** → **Blueprint**  
3. Connect **BashayerNoury/Bookmark**, branch **`stage`** (see `render.yaml`)  
4. Set secret **`GEMINI_API_KEY`**  
5. Deploy → `https://bookmark-xxxx.onrender.com`

**Manual web service**

| Setting | Value |
|---------|--------|
| Build | `chmod +x build.sh && ./build.sh` |
| Start | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT` |
| Env | `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com`, `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.1-flash-lite` |

**Notes:** free tier sleeps when idle; SQLite is fine for demos (may reset on redeploy).

---

## API

### Chat

`POST /api/chat/`

```json
{
  "message": "cozy fantasy with found family",
  "history": [],
  "limit": 4
}
```

```json
{
  "reply": "…",
  "books": [
    {
      "id": 123,
      "title": "…",
      "author": "…",
      "isbn": "…",
      "cover_url": "https://covers.openlibrary.org/…",
      "genres": [{ "name": "…" }],
      "tags": []
    }
  ]
}
```

Other endpoints (auth, books CRUD, legacy recommend) exist under `/api/` for admin and future features; the live chat UI only needs `/api/chat/`.

---

## Project layout

```text
Bookmark/
├── accounts/          # User profile helpers
├── books/             # Chat, Gemini, Open Library, models, admin
├── config/            # Django settings, URLs, WSGI
├── frontend/          # React + Vite chat app
│   └── src/
│       ├── App.jsx    # Full chat UI
│       ├── api.js
│       └── index.css  # Brand tokens (colors, themes)
├── build.sh           # Render / production build
├── render.yaml        # Render Blueprint
├── manage.py
└── requirements.txt
```

---

## License / intent

Personal / portfolio product by Bashayer. Use and adapt freely for learning and demos.
