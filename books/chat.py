"""
Conversational book recommender for the Bookmark chat UI.

Uses Google Gemini for suggestions and Open Library for covers/ISBNs.
No local catalog matching.
"""

from __future__ import annotations

import hashlib
import re

from .gemini import gemini_recommend
from .models import GoodreadsTasteProfile
from .openlibrary import enrich_book


GREETINGS = {'hi', 'hello', 'hey', 'yo', 'sup', 'howdy'}
HELP_PHRASES = ('what can you', 'help', 'how do you', 'what do you do')


def _is_greeting(text: str) -> bool:
    cleaned = re.sub(r'[^a-z\s]', '', text.lower()).strip()
    tokens = cleaned.split()
    return len(tokens) <= 4 and any(t in GREETINGS for t in tokens)


def _wants_help(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in HELP_PHRASES)


def _stable_id(title: str, author: str) -> int:
    digest = hashlib.sha1(f'{title}|{author}'.encode('utf-8')).hexdigest()
    return int(digest[:8], 16)


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
                'Hi — I’m Bookmark, your AI book recommendation chat powered by Google Gemini. '
                'Ask me things like “cozy fantasy with found family,” '
                '“something dark and twisty,” or “books like Project Hail Mary.”'
            ),
            'books': [],
        }

    if _wants_help(text):
        return {
            'reply': (
                'I use Google Gemini to recommend real books worldwide, then pull covers and details from Open Library. '
                'Try a mood, genre, themes, or “more like …” a title you love. '
                'Tap any book card to open it on Goodreads.'
            ),
            'books': [],
        }

    taste_profile = None
    if user and user.is_authenticated:
        taste_profile = GoodreadsTasteProfile.objects.filter(user=user).first()

    ai = gemini_recommend(
        message=text,
        history=history,
        taste_profile=taste_profile,
        limit=limit,
    )
    if ai.get('error') == 'missing_api_key':
        return {
            'reply': (
                'AI recommendations need a free Google Gemini API key. '
                'Add `GEMINI_API_KEY` to your `.env` from https://aistudio.google.com/apikey, '
                'then restart the server.'
            ),
            'books': [],
            'provider': 'none',
        }
    if ai.get('error'):
        return {
            'reply': (
                'Bookmark could not get recommendations from Google Gemini right now. '
                'Check that `GEMINI_API_KEY` and `GEMINI_MODEL` are valid, then try again.'
            ),
            'books': [],
            'provider': 'none',
        }

    books = []
    for item in ai['books']:
        enriched = enrich_book(item['title'], item['author'])
        enriched['id'] = _stable_id(enriched['title'], enriched['author'])
        if item.get('reason') and not enriched.get('description'):
            enriched['description'] = item['reason']
        books.append(enriched)

    return {
        'reply': (
            f'Based on your Goodreads history, {ai["reply"]}'
            if taste_profile else ai['reply']
        ),
        'books': books,
        'provider': 'gemini',
    }
