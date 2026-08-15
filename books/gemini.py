"""
Google Gemini client for Bookmark chat recommendations.

Free-tier Generative Language API. Recommends real-world books (not a local catalog).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse

from django.conf import settings

from .http_util import http_json


def gemini_recommend(*, message: str, history=None, taste_profile=None, limit: int = 4) -> dict | None:
    """
    Ask Gemini for book recommendations.
    Returns {'reply': str, 'books': [{'title','author','reason'}, ...]} or None.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    if not api_key:
        return None

    history = history or []
    model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash') or 'gemini-2.0-flash'
    history_lines = []
    for turn in history[-8:]:
        role = turn.get('role', 'user')
        content = (turn.get('content') or '').strip()
        if content:
            history_lines.append(f'{role}: {content}')

    taste_context = '(No Goodreads profile imported yet.)'
    if taste_profile:
        favorite_authors = ', '.join(
            item.get('name', '') for item in taste_profile.favorite_authors[:8]
            if item.get('name')
        )
        favorite_shelves = ', '.join(
            item.get('name', '') for item in taste_profile.favorite_shelves[:8]
            if item.get('name')
        )
        liked_titles = ', '.join(
            item.get('title', '') for item in taste_profile.liked_books[:15]
            if item.get('title')
        )
        disliked_titles = ', '.join(
            item.get('title', '') for item in taste_profile.disliked_books[:10]
            if item.get('title')
        )
        read_titles = ', '.join(
            item.get('title', '') for item in taste_profile.reading_history[:80]
            if item.get('title')
        )
        taste_context = (
            f'Favorite authors: {favorite_authors or "unknown"}\n'
            f'Favorite shelves/themes: {favorite_shelves or "unknown"}\n'
            f'Highly rated books: {liked_titles or "unknown"}\n'
            f'Lower rated books: {disliked_titles or "unknown"}\n'
            f'Already read (do not recommend these): {read_titles or "unknown"}'
        )

    prompt = (
        'You are Bookmark, a warm book-recommendation chatbot like ChatGPT.\n'
        'Recommend real, well-known published books that match the reader.\n'
        f'Suggest exactly {limit} books when possible (fewer only if the request is tiny).\n'
        'Prefer widely available titles. Do not invent fake books.\n'
        'Write a conversational reply that mentions each pick with **Title** and a short why.\n'
        'Return ONLY valid JSON with this shape:\n'
        '{\n'
        '  "reply": "markdown-friendly plain text",\n'
        '  "books": [\n'
        '    {"title": "Exact title", "author": "Author name", "reason": "one short sentence"}\n'
        '  ]\n'
        '}\n\n'
        f'Recent chat:\n{chr(10).join(history_lines) or "(none)"}\n\n'
        f'Reader Goodreads taste:\n{taste_context}\n\n'
        f'Reader message:\n{message}'
    )

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{urllib.parse.quote(model)}:generateContent'
        f'?key={urllib.parse.quote(api_key)}'
    )
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.8,
            'maxOutputTokens': 900,
            'responseMimeType': 'application/json',
        },
    }
    try:
        data = http_json(url, data=payload, timeout=30)
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

    reply = (parsed.get('reply') or '').strip()
    raw_books = parsed.get('books') or []
    books = []
    for item in raw_books:
        if not isinstance(item, dict):
            continue
        title = (item.get('title') or '').strip()
        author = (item.get('author') or '').strip()
        if not title:
            continue
        books.append({
            'title': title,
            'author': author,
            'reason': (item.get('reason') or '').strip(),
        })
        if len(books) >= limit:
            break

    if not reply or not books:
        return None

    return {'reply': reply, 'books': books}
