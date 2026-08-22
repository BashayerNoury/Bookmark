"""
Google Gemini client for Bookmark chat recommendations.

Free-tier Generative Language API. Recommends real-world books (not a local catalog).
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse

from django.conf import settings

from .http_util import http_json


# Prefer models currently available to new Gemini API keys.
_FALLBACK_MODELS = (
    'gemini-3.1-flash-lite',
    'gemini-flash-latest',
    'gemini-flash-lite-latest',
    'gemini-3.5-flash',
)


def _model_candidates(preferred: str) -> list[str]:
    models = [preferred]
    for model in _FALLBACK_MODELS:
        if model not in models:
            models.append(model)
    return models


def _parse_json_payload(text: str) -> dict:
    text = (text or '').strip()
    if not text:
        raise json.JSONDecodeError('empty', text, 0)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.*\}', text, flags=re.DOTALL)
    if not match:
        raise json.JSONDecodeError('no-object', text, 0)
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError('parsed payload is not an object')
    return parsed


def _normalize_books(raw_books, limit: int) -> list[dict]:
    books = []
    for item in raw_books or []:
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
    return books


def gemini_recommend(*, message: str, history=None, taste_profile=None, limit: int = 4) -> dict:
    """
    Ask Gemini for book recommendations.
    Returns {'reply': str, 'books': [...]} on success, or {'error': str, ...} on failure.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    preferred = getattr(settings, 'GEMINI_MODEL', 'gemini-3.1-flash-lite') or 'gemini-3.1-flash-lite'
    if not api_key:
        return {'error': 'missing_api_key'}

    history = history or []
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
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.8,
            'maxOutputTokens': 900,
            'responseMimeType': 'application/json',
        },
    }

    last_error: dict | None = None
    for model in _model_candidates(preferred):
        url = (
            f'https://generativelanguage.googleapis.com/v1beta/models/'
            f'{urllib.parse.quote(model)}:generateContent'
            f'?key={urllib.parse.quote(api_key)}'
        )
        try:
            data = http_json(url, data=payload, timeout=30)
            text = data['candidates'][0]['content']['parts'][0]['text']
            parsed = _parse_json_payload(text)
        except (
            urllib.error.URLError,
            TimeoutError,
            KeyError,
            IndexError,
            TypeError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            status = getattr(exc, 'code', None)
            last_error = {
                'error': 'upstream_failed',
                'error_type': type(exc).__name__,
                'http_status': status,
                'model': model,
            }
            # Retry on unavailable / retired models and temporary overload.
            if status in {404, 429, 503}:
                continue
            return last_error

        reply = (parsed.get('reply') or '').strip()
        books = _normalize_books(parsed.get('books'), limit)
        if not reply or not books:
            last_error = {'error': 'invalid_response', 'model': model}
            continue

        return {'reply': reply, 'books': books, 'model': model}

    return last_error or {'error': 'upstream_failed', 'model': preferred}
