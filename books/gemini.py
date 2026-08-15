"""
Google Gemini client for Bookmark chat recommendations.

Uses the free-tier Generative Language API. Requires GEMINI_API_KEY.
Books are always chosen from the provided catalog candidates so titles/covers stay real.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings


def _catalog_payload(books) -> list[dict]:
    rows = []
    for book in books:
        genres = [g.name for g in book.genres.all()[:3]]
        rows.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'genres': genres,
            'tags': (book.tags or [])[:6],
            'description': (book.description or '')[:220],
            'average_rating': float(book.average_rating or 0),
        })
    return rows


def gemini_recommend(*, message: str, history=None, candidates=None, limit: int = 4) -> dict | None:
    """
    Ask Gemini to pick books from candidates and write a chat reply.
    Returns {'reply': str, 'book_ids': list[int]} or None on failure / missing key.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    if not api_key:
        return None

    candidates = list(candidates or [])
    if not candidates:
        return None

    history = history or []
    model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash') or 'gemini-2.0-flash'
    catalog = _catalog_payload(candidates)
    history_lines = []
    for turn in history[-8:]:
        role = turn.get('role', 'user')
        content = (turn.get('content') or '').strip()
        if content:
            history_lines.append(f'{role}: {content}')

    prompt = (
        'You are Bookmark, a warm book-recommendation chatbot.\n'
        'Recommend ONLY from the catalog JSON below. Never invent titles.\n'
        f'Pick up to {limit} books that best match the reader.\n'
        'Reply in a conversational tone (like ChatGPT), use **title** for book names, '
        'and briefly say why each fits.\n'
        'Return ONLY valid JSON with this shape:\n'
        '{"reply": "markdown-friendly plain text", "book_ids": [1, 2]}\n\n'
        f'Recent chat:\n{chr(10).join(history_lines) or "(none)"}\n\n'
        f'Reader message:\n{message}\n\n'
        f'Catalog:\n{json.dumps(catalog, ensure_ascii=False)}'
    )

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{urllib.parse.quote(model)}:generateContent'
        f'?key={urllib.parse.quote(api_key)}'
    )
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 700,
            'responseMimeType': 'application/json',
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        text = data['candidates'][0]['content']['parts'][0]['text']
        parsed = json.loads(text)
    except (
        urllib.error.URLError,
        TimeoutError,
        KeyError,
        IndexError,
        TypeError,
        json.JSONDecodeError,
        ValueError,
    ):
        return None

    allowed = {b.id for b in candidates}
    raw_ids = parsed.get('book_ids') or []
    book_ids = []
    for item in raw_ids:
        try:
            bid = int(item)
        except (TypeError, ValueError):
            continue
        if bid in allowed and bid not in book_ids:
            book_ids.append(bid)
        if len(book_ids) >= limit:
            break

    reply = (parsed.get('reply') or '').strip()
    if not reply or not book_ids:
        return None

    return {'reply': reply, 'book_ids': book_ids}
