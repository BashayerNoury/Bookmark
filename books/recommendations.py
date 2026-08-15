"""
AI-style book recommendation engine.

Uses preference matching over genres, tags, ratings, and bookmarks.
When OPENAI_API_KEY is set, optionally enriches the explanation with
a short natural-language rationale (never required to function).
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from collections import Counter

from django.conf import settings
from django.db.models import Q

from .models import Book, Bookmark, RecommendationLog


MOOD_KEYWORDS = {
    'cozy': ['cozy', 'comfort', 'warm', 'gentle', 'domestic'],
    'dark': ['dark', 'grim', 'noir', 'tragic', 'dystopian'],
    'adventurous': ['adventure', 'quest', 'journey', 'epic', 'explore'],
    'romantic': ['romance', 'love', 'relationship', 'heart'],
    'thoughtful': ['philosophy', 'literary', 'reflective', 'literary fiction'],
    'thrilling': ['thriller', 'suspense', 'mystery', 'crime', 'spy'],
    'funny': ['humor', 'comedy', 'funny', 'satire', 'witty'],
    'inspiring': ['memoir', 'self-help', 'biography', 'inspirational'],
}


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r'[a-z0-9]+', (text or '').lower()) if len(t) > 2}


def _score_book(book: Book, preferred_genres: Counter, preferred_tags: Counter, query_tokens: set[str], mood: str) -> float:
    score = float(book.average_rating or 0) * 1.5

    for genre in book.genres.all():
        score += preferred_genres.get(genre.slug, 0) * 3
        score += preferred_genres.get(genre.name.lower(), 0) * 3

    for tag in book.tags or []:
        score += preferred_tags.get(tag.lower(), 0) * 2

    haystack = _tokenize(f'{book.title} {book.author} {book.description} {" ".join(book.tags or [])}')
    score += len(query_tokens & haystack) * 4

    if mood:
        mood_keys = MOOD_KEYWORDS.get(mood.lower(), [mood.lower()])
        genre_names = {g.name.lower() for g in book.genres.all()}
        tag_names = {t.lower() for t in (book.tags or [])}
        for key in mood_keys:
            if key in haystack or key in genre_names or key in tag_names:
                score += 5

    return score


def _openai_explanation(query: str, mood: str, books: list[Book]) -> str | None:
    api_key = getattr(settings, 'OPENAI_API_KEY', '') or ''
    if not api_key or not books:
        return None

    titles = ', '.join(f'{b.title} by {b.author}' for b in books[:5])
    prompt = (
        f'In 2 short sentences, explain why these books fit someone looking for '
        f'"{query or "great reads"}" with mood "{mood or "any"}": {titles}. '
        'Be warm and specific. No bullet points.'
    )
    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': 'You are a friendly literary recommender for the Bookmark app.'},
            {'role': 'user', 'content': prompt},
        ],
        'max_tokens': 120,
        'temperature': 0.7,
    }
    req = urllib.request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return data['choices'][0]['message']['content'].strip()
    except (urllib.error.URLError, KeyError, IndexError, TimeoutError, json.JSONDecodeError):
        return None


def recommend_books(*, user=None, query: str = '', mood: str = '', limit: int = 6):
    preferred_genres: Counter = Counter()
    preferred_tags: Counter = Counter()
    exclude_ids: set[int] = set()

    if user and user.is_authenticated:
        bookmarks = Bookmark.objects.filter(user=user).select_related('book').prefetch_related('book__genres')
        for bm in bookmarks:
            exclude_ids.add(bm.book_id)
            weight = 3 if bm.status == Bookmark.STATUS_FINISHED else 2 if bm.status == Bookmark.STATUS_READING else 1
            for genre in bm.book.genres.all():
                preferred_genres[genre.slug] += weight
                preferred_genres[genre.name.lower()] += weight
            for tag in bm.book.tags or []:
                preferred_tags[tag.lower()] += weight

        if hasattr(user, 'profile'):
            for g in user.profile.favorite_genres or []:
                preferred_genres[str(g).lower()] += 2

    query_tokens = _tokenize(query)
    if mood:
        query_tokens |= _tokenize(mood)
        for key in MOOD_KEYWORDS.get(mood.lower(), []):
            query_tokens.add(key)

    qs = Book.objects.prefetch_related('genres').all()
    if exclude_ids:
        qs = qs.exclude(id__in=exclude_ids)

    # Soft filter when query looks genre-specific
    if query_tokens:
        genre_q = Q()
        for token in query_tokens:
            genre_q |= Q(genres__slug__icontains=token) | Q(genres__name__icontains=token) | Q(tags__icontains=token)
        filtered = qs.filter(genre_q).distinct()
        if filtered.exists():
            qs = filtered

    scored = sorted(
        ((_score_book(book, preferred_genres, preferred_tags, query_tokens, mood), book) for book in qs),
        key=lambda pair: pair[0],
        reverse=True,
    )

    top = [book for _, book in scored[:limit]]
    if not top:
        top = list(Book.objects.order_by('-average_rating')[:limit])

    explanation = _openai_explanation(query, mood, top)
    if not explanation:
        parts = []
        if mood:
            parts.append(f'tuned for a {mood} mood')
        if query:
            parts.append(f'matching “{query}”')
        if user and user.is_authenticated and preferred_genres:
            top_genres = ', '.join(g for g, _ in preferred_genres.most_common(2))
            parts.append(f'based on your taste for {top_genres}')
        if not parts:
            parts.append('based on reader ratings and popular titles in our catalog')
        explanation = 'Here are picks ' + ' and '.join(parts) + '.'

    if user and user.is_authenticated:
        RecommendationLog.objects.create(
            user=user,
            query=query,
            mood=mood,
            result_ids=[b.id for b in top],
            explanation=explanation,
        )

    return top, explanation
