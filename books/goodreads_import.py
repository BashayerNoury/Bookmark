"""Safe parsing and aggregation for a Goodreads Library Export CSV."""

from __future__ import annotations

import csv
import io
from collections import Counter

MAX_ROWS = 10_000
MAX_FILE_SIZE = 10 * 1024 * 1024
REQUIRED_COLUMNS = {'Title', 'Author'}


def _clean(value: str | None) -> str:
    return (value or '').strip()


def _rating(value: str | None) -> int:
    try:
        score = int(_clean(value) or 0)
    except ValueError:
        return 0
    return score if 0 <= score <= 5 else 0


def parse_goodreads_csv(uploaded_file) -> dict:
    """Parse a Goodreads export in memory and build a compact taste summary."""
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValueError('The CSV is too large. Upload a file under 10 MB.')
    if not uploaded_file.name.lower().endswith('.csv'):
        raise ValueError('Upload a Goodreads Library Export CSV file.')

    try:
        text = uploaded_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError('This file is not a readable UTF-8 Goodreads CSV.') from exc

    fields = set(reader.fieldnames or [])
    if not REQUIRED_COLUMNS.issubset(fields):
        raise ValueError('This does not look like a Goodreads Library Export (Title and Author are required).')

    authors = Counter()
    shelves = Counter()
    liked_books = []
    disliked_books = []
    reading_history = []
    ratings = Counter()
    valid_rows = 0
    total_rows = 0

    for row in reader:
        total_rows += 1
        if total_rows > MAX_ROWS:
            raise ValueError(f'The CSV has more than {MAX_ROWS:,} rows. Split it into smaller imports.')

        title = _clean(row.get('Title'))
        author = _clean(row.get('Author'))
        if not title or not author:
            continue

        valid_rows += 1
        rating = _rating(row.get('My Rating'))
        shelf = _clean(row.get('Exclusive Shelf')).lower() or 'unknown'
        custom_shelves = [
            item.strip()
            for item in _clean(row.get('Bookshelves')).split(',')
            if item.strip()
        ]
        isbn = _clean(row.get('ISBN13')) or _clean(row.get('ISBN'))
        isbn = ''.join(char for char in isbn if char.isdigit() or char.upper() == 'X')

        if rating:
            ratings[str(rating)] += 1

        # Completed, highly-rated books are strongest signals.
        weight = 1
        if shelf == 'read':
            weight += 2
        if rating >= 4:
            weight += rating - 2
        elif rating and rating <= 2:
            weight = -2

        if weight > 0:
            authors[author] += weight
            shelves[shelf] += weight
            for custom_shelf in custom_shelves:
                shelves[custom_shelf.lower()] += max(1, weight // 2)

        record = {
            'title': title,
            'author': author,
            'rating': rating,
            'shelf': shelf,
            'isbn': isbn,
        }
        if shelf == 'read' or rating:
            reading_history.append(record)
        if rating >= 4:
            liked_books.append(record)
        elif 0 < rating <= 2:
            disliked_books.append(record)

    if not valid_rows:
        raise ValueError('No valid books were found in this CSV.')

    return {
        'total_rows': total_rows,
        'valid_rows': valid_rows,
        'favorite_authors': [
            {'name': name, 'weight': weight}
            for name, weight in authors.most_common(12)
        ],
        'favorite_shelves': [
            {'name': name, 'weight': weight}
            for name, weight in shelves.most_common(12)
            if name not in {'to-read', 'currently-reading', 'unknown'}
        ],
        'liked_books': liked_books[:80],
        'disliked_books': disliked_books[:40],
        'reading_history': reading_history[:500],
        'rating_summary': {
            'counts': dict(ratings),
            'average': round(
                sum(int(score) * count for score, count in ratings.items()) / sum(ratings.values()),
                2,
            ) if ratings else None,
        },
    }
