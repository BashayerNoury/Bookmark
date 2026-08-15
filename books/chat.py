"""
Conversational book recommender for the Bookmark chat UI.
"""

from __future__ import annotations

import re

from .recommendations import MOOD_KEYWORDS, recommend_books


GREETINGS = {'hi', 'hello', 'hey', 'yo', 'sup', 'howdy'}
HELP_PHRASES = ('what can you', 'help', 'how do you', 'what do you do')


def _detect_mood(text: str) -> str:
    lower = text.lower()
    for mood, keys in MOOD_KEYWORDS.items():
        if mood in lower or any(k in lower for k in keys):
            return mood
    return ''


def _is_greeting(text: str) -> bool:
    cleaned = re.sub(r'[^a-z\s]', '', text.lower()).strip()
    tokens = cleaned.split()
    return len(tokens) <= 4 and any(t in GREETINGS for t in tokens)


def _wants_help(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in HELP_PHRASES)


def chat_reply(*, message: str, history=None, user=None, limit: int = 4):
    text = (message or '').strip()
    history = history or []

    if not text:
        return {
            'reply': 'Tell me what you’re in the mood to read — a vibe, genre, author, or book you loved.',
            'books': [],
        }

    if _is_greeting(text) and len(text) < 40:
        return {
            'reply': (
                'Hi — I’m Bookmark, your book recommendation chat. '
                'Ask me things like “cozy fantasy with found family,” '
                '“something dark and twisty,” or “books like Project Hail Mary.”'
            ),
            'books': [],
        }

    if _wants_help(text):
        return {
            'reply': (
                'I recommend books from Bookmark’s catalog based on what you say. '
                'Try a mood (cozy, dark, thrilling), a genre, themes, or “more like …” a title you love. '
                'I’ll reply with picks and why they fit.'
            ),
            'books': [],
        }

    # Fold recent user turns into the query for better continuity
    prior_user = [
        m.get('content', '')
        for m in history[-6:]
        if m.get('role') == 'user' and m.get('content')
    ]
    combined_query = ' '.join(prior_user + [text]).strip()
    mood = _detect_mood(text) or _detect_mood(combined_query)

    books, explanation = recommend_books(
        user=user,
        query=text,
        mood=mood,
        limit=limit,
    )

    if not books:
        return {
            'reply': (
                'I couldn’t find a strong match in the catalog for that. '
                'Try another angle — e.g. “funny mystery,” “literary sci-fi,” or “inspiring memoir.”'
            ),
            'books': [],
        }

    lines = [
        explanation.rstrip('.').rstrip() + '.',
        '',
        'Here are my picks:',
    ]
    for i, book in enumerate(books, start=1):
        genres = ', '.join(g.name for g in book.genres.all()[:2]) or 'General'
        lines.append(
            f'{i}. **{book.title}** by {book.author} — {genres}. {book.description[:140].rstrip(".")}.'
        )
    lines.append('')
    lines.append('Want different vibes, more like one of these, or a shorter / longer read? Just say.')

    return {
        'reply': '\n'.join(lines),
        'books': books,
        'explanation': explanation,
    }
