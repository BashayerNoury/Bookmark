from django.core.management.base import BaseCommand
from django.utils.text import slugify

from books.models import Book, Genre


def open_library_cover(isbn):
    # default=false → 404 when missing (so the UI can fall back) instead of a 1×1 GIF
    return f'https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false'


CATALOG = [
    {
        'title': 'Project Hail Mary',
        'author': 'Andy Weir',
        'description': 'A lone astronaut wakes up millions of miles from home with no memory—and a mission to save humanity.',
        'genres': ['Science Fiction'],
        'tags': ['space', 'survival', 'humor', 'adventure'],
        'cover_color': '#1B4F72',
        'isbn': '9780593135204',
        'published_year': 2021,
        'page_count': 476,
        'average_rating': 4.6,
        'ratings_count': 210,
    },
    {
        'title': 'The Midnight Library',
        'author': 'Matt Haig',
        'description': 'Between life and death there is a library where every book is a different life Nora Seed could have lived.',
        'genres': ['Literary Fiction', 'Fantasy'],
        'tags': ['parallel lives', 'philosophy', 'hope', 'reflective'],
        'cover_color': '#5B2C6F',
        'isbn': '9780525559474',
        'published_year': 2020,
        'page_count': 304,
        'average_rating': 4.2,
        'ratings_count': 340,
    },
    {
        'title': 'Klara and the Sun',
        'author': 'Kazuo Ishiguro',
        'description': 'An Artificial Friend observes the mysterious human world with quiet devotion and unsettling clarity.',
        'genres': ['Literary Fiction', 'Science Fiction'],
        'tags': ['ai', 'love', 'literary', 'reflective'],
        'cover_color': '#B9770E',
        'isbn': '9780593318171',
        'published_year': 2021,
        'page_count': 303,
        'average_rating': 4.1,
        'ratings_count': 180,
    },
    {
        'title': 'The Silent Patient',
        'author': 'Alex Michaelides',
        'description': 'A famous painter shoots her husband and never speaks again. A psychotherapist is determined to uncover why.',
        'genres': ['Thriller', 'Mystery'],
        'tags': ['suspense', 'twist', 'psychological', 'crime'],
        'cover_color': '#922B21',
        'isbn': '9781250301697',
        'published_year': 2019,
        'page_count': 336,
        'average_rating': 4.3,
        'ratings_count': 410,
    },
    {
        'title': 'Circe',
        'author': 'Madeline Miller',
        'description': 'The witch of Aiaia tells her own mythic story of exile, power, and becoming.',
        'genres': ['Fantasy', 'Historical Fiction'],
        'tags': ['mythology', 'feminist', 'epic', 'magic'],
        'cover_color': '#1A5276',
        'isbn': '9780316556347',
        'published_year': 2018,
        'page_count': 393,
        'average_rating': 4.5,
        'ratings_count': 390,
    },
    {
        'title': 'Atomic Habits',
        'author': 'James Clear',
        'description': 'Tiny changes, remarkable results—a practical framework for building better habits every day.',
        'genres': ['Self-Help'],
        'tags': ['habits', 'productivity', 'inspirational'],
        'cover_color': '#196F3D',
        'isbn': '9780735211292',
        'published_year': 2018,
        'page_count': 320,
        'average_rating': 4.4,
        'ratings_count': 520,
    },
    {
        'title': 'Piranesi',
        'author': 'Susanna Clarke',
        'description': 'In a house of endless halls and drowning statues, a gentle soul catalogs wonders—and a mystery.',
        'genres': ['Fantasy', 'Literary Fiction'],
        'tags': ['surreal', 'mystery', 'cozy', 'literary'],
        'cover_color': '#2874A6',
        'isbn': '9781635575637',
        'published_year': 2020,
        'page_count': 272,
        'average_rating': 4.4,
        'ratings_count': 250,
    },
    {
        'title': 'Educated',
        'author': 'Tara Westover',
        'description': 'A memoir of a woman who leaves her survivalist family and earns a Cambridge PhD.',
        'genres': ['Memoir', 'Biography'],
        'tags': ['memoir', 'education', 'resilience', 'inspirational'],
        'cover_color': '#6E2C00',
        'isbn': '9780399590504',
        'published_year': 2018,
        'page_count': 334,
        'average_rating': 4.5,
        'ratings_count': 480,
    },
    {
        'title': 'The House in the Cerulean Sea',
        'author': 'TJ Klune',
        'description': 'A by-the-book caseworker is sent to a magical orphanage that will change his carefully ordered life.',
        'genres': ['Fantasy', 'Romance'],
        'tags': ['cozy', 'found family', 'queer', 'warm'],
        'cover_color': '#1ABC9C',
        'isbn': '9781250217288',
        'published_year': 2020,
        'page_count': 398,
        'average_rating': 4.6,
        'ratings_count': 360,
    },
    {
        'title': 'Gone Girl',
        'author': 'Gillian Flynn',
        'description': 'On their fifth wedding anniversary, Amy Dunne disappears—and Nick becomes the prime suspect.',
        'genres': ['Thriller', 'Mystery'],
        'tags': ['dark', 'marriage', 'suspense', 'twist'],
        'cover_color': '#4A235A',
        'isbn': '9780307588371',
        'published_year': 2012,
        'page_count': 422,
        'average_rating': 4.1,
        'ratings_count': 600,
    },
    {
        'title': 'Dune',
        'author': 'Frank Herbert',
        'description': 'On the desert planet Arrakis, young Paul Atreides is swept into prophecy, power, and rebellion.',
        'genres': ['Science Fiction', 'Fantasy'],
        'tags': ['epic', 'politics', 'adventure', 'classic'],
        'cover_color': '#7D6608',
        'isbn': '9780441172719',
        'published_year': 1965,
        'page_count': 688,
        'average_rating': 4.4,
        'ratings_count': 900,
    },
    {
        'title': 'Normal People',
        'author': 'Sally Rooney',
        'description': 'Connell and Marianne navigate intimacy, class, and miscommunication from school to university.',
        'genres': ['Literary Fiction', 'Romance'],
        'tags': ['relationships', 'literary', 'coming of age'],
        'cover_color': '#884EA0',
        'isbn': '9781984822178',
        'published_year': 2018,
        'page_count': 273,
        'average_rating': 3.9,
        'ratings_count': 430,
    },
    {
        'title': 'The Thursday Murder Club',
        'author': 'Richard Osman',
        'description': 'Four retirees in a peaceful village take on an unsolved murder—with wit and unexpected skill.',
        'genres': ['Mystery', 'Humor'],
        'tags': ['cozy', 'crime', 'funny', 'friendship'],
        'cover_color': '#148F77',
        'isbn': '9781984880987',
        'published_year': 2020,
        'page_count': 368,
        'average_rating': 4.2,
        'ratings_count': 310,
    },
    {
        'title': 'Sapiens',
        'author': 'Yuval Noah Harari',
        'description': 'A sweeping history of humankind—from foraging bands to global empires and beyond.',
        'genres': ['Nonfiction', 'History'],
        'tags': ['history', 'anthropology', 'thoughtful', 'big ideas'],
        'cover_color': '#CA6F1E',
        'isbn': '9780062316097',
        'published_year': 2011,
        'page_count': 443,
        'average_rating': 4.3,
        'ratings_count': 700,
    },
    {
        'title': 'Mexican Gothic',
        'author': 'Silvia Moreno-Garcia',
        'description': 'A glamorous socialite investigates a haunted mansion in 1950s rural Mexico.',
        'genres': ['Horror', 'Historical Fiction'],
        'tags': ['gothic', 'dark', 'haunted', 'suspense'],
        'cover_color': '#145A32',
        'isbn': '9780525620785',
        'published_year': 2020,
        'page_count': 320,
        'average_rating': 4.0,
        'ratings_count': 280,
    },
    {
        'title': 'A Court of Thorns and Roses',
        'author': 'Sarah J. Maas',
        'description': 'A huntress is taken to a magical land after killing a wolf—and discovers a cursed faerie realm.',
        'genres': ['Fantasy', 'Romance'],
        'tags': ['fae', 'romance', 'adventure', 'epic'],
        'cover_color': '#9B2335',
        'isbn': '9781635575569',
        'published_year': 2015,
        'page_count': 419,
        'average_rating': 4.3,
        'ratings_count': 850,
    },
    {
        'title': 'The Anthropocene Reviewed',
        'author': 'John Green',
        'description': 'Essays rating facets of the human-centered planet—on a five-star scale, with warmth and wit.',
        'genres': ['Essays', 'Nonfiction'],
        'tags': ['essays', 'reflective', 'funny', 'hope'],
        'cover_color': '#21618C',
        'isbn': '9780525555216',
        'published_year': 2021,
        'page_count': 304,
        'average_rating': 4.5,
        'ratings_count': 200,
    },
    {
        'title': 'The Seven Husbands of Evelyn Hugo',
        'author': 'Taylor Jenkins Reid',
        'description': 'A reclusive Hollywood icon finally tells the truth about her glamorous, carefully constructed life.',
        'genres': ['Historical Fiction', 'Romance'],
        'tags': ['hollywood', 'queer', 'secrets', 'glamour'],
        'cover_color': '#C0392B',
        'isbn': '9781501161940',
        'published_year': 2017,
        'page_count': 400,
        'average_rating': 4.5,
        'ratings_count': 620,
    },
]


class Command(BaseCommand):
    help = 'Seed genres and sample books for Bookmark'

    def handle(self, *args, **options):
        genre_cache = {}
        for entry in CATALOG:
            for name in entry['genres']:
                if name not in genre_cache:
                    genre, _ = Genre.objects.get_or_create(
                        slug=slugify(name),
                        defaults={'name': name},
                    )
                    genre_cache[name] = genre

        created = 0
        for entry in CATALOG:
            isbn = entry.get('isbn', '')
            cover_url = entry.get('cover_url') or (open_library_cover(isbn) if isbn else '')
            book, was_created = Book.objects.update_or_create(
                title=entry['title'],
                author=entry['author'],
                defaults={
                    'description': entry['description'],
                    'cover_color': entry['cover_color'],
                    'cover_url': cover_url,
                    'isbn': isbn,
                    'published_year': entry['published_year'],
                    'page_count': entry['page_count'],
                    'average_rating': entry['average_rating'],
                    'ratings_count': entry['ratings_count'],
                    'tags': entry['tags'],
                },
            )
            book.genres.set([genre_cache[g] for g in entry['genres']])
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {Genre.objects.count()} genres and {Book.objects.count()} books ({created} new).'
        ))
