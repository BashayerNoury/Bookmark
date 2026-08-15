"""
Open Library helpers — free metadata/covers for AI-suggested books.
"""

from __future__ import annotations

import urllib.error
import urllib.parse

from .http_util import http_json


def open_library_cover_url(*, isbn: str = '', cover_id=None) -> str:
    if isbn:
        return f'https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false'
    if cover_id:
        return f'https://covers.openlibrary.org/b/id/{cover_id}-M.jpg?default=false'
    return ''


def enrich_book(title: str, author: str = '') -> dict:
    """
    Look up a title/author on Open Library and return UI-ready book fields.
    Always returns a dict (falls back to title/author only if lookup fails).
    """
    title = (title or '').strip()
    author = (author or '').strip()
    query = ' '.join(part for part in (title, author) if part)
    base = {
        'title': title or 'Unknown',
        'author': author or 'Unknown',
        'description': '',
        'isbn': '',
        'cover_url': '',
        'cover_color': '#800020',
        'published_year': None,
        'page_count': None,
        'average_rating': 0,
        'ratings_count': 0,
        'genres': [],
        'tags': [],
        'is_bookmarked': False,
    }
    if not query:
        return base

    url = 'https://openlibrary.org/search.json?' + urllib.parse.urlencode({
        'q': query,
        'limit': 1,
        'fields': 'key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median',
    })
    try:
        data = http_json(url, timeout=10)
        docs = data.get('docs') or []
        if not docs:
            return base
        doc = docs[0]
    except (urllib.error.URLError, TimeoutError, KeyError, TypeError, ValueError):
        return base

    isbns = doc.get('isbn') or []
    isbn = ''
    for candidate in isbns:
        digits = ''.join(c for c in str(candidate) if c.isdigit() or c.upper() == 'X')
        if len(digits) == 13 and digits.isdigit():
            isbn = digits
            break
        if len(digits) == 10 and not isbn:
            isbn = digits

    subjects = [s for s in (doc.get('subject') or []) if isinstance(s, str)][:4]
    authors = doc.get('author_name') or []
    cover_id = doc.get('cover_i')
    cover_url = open_library_cover_url(isbn=isbn, cover_id=cover_id)

    return {
        **base,
        'title': doc.get('title') or title,
        'author': authors[0] if authors else author,
        'isbn': isbn,
        'cover_url': cover_url,
        'published_year': doc.get('first_publish_year'),
        'page_count': doc.get('number_of_pages_median'),
        'genres': [
            {'id': i + 1, 'name': s, 'slug': s.lower().replace(' ', '-')}
            for i, s in enumerate(subjects[:2])
        ],
        'tags': subjects[:6],
    }
