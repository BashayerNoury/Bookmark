from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .goodreads_import import parse_goodreads_csv


class GoodreadsImportTests(TestCase):
    def test_parser_builds_taste_summary(self):
        csv_data = (
            'Book Id,Title,Author,My Rating,Exclusive Shelf,Bookshelves,ISBN,ISBN13\n'
            '1,Dune,Frank Herbert,5,read,science-fiction,9780441172719,9780441172719\n'
            '2,Example,Someone,1,read,not-for-me,,\n'
        )
        upload = SimpleUploadedFile('goodreads_library_export.csv', csv_data.encode('utf-8'), 'text/csv')

        summary = parse_goodreads_csv(upload)

        self.assertEqual(summary['valid_rows'], 2)
        self.assertEqual(summary['favorite_authors'][0]['name'], 'Frank Herbert')
        self.assertEqual(summary['liked_books'][0]['title'], 'Dune')

    def test_authenticated_import_creates_profile(self):
        user = User.objects.create_user(username='reader', password='safe-password')
        client = APIClient()
        client.force_authenticate(user)
        csv_data = (
            'Book Id,Title,Author,My Rating,Exclusive Shelf,Bookshelves\n'
            '1,Dune,Frank Herbert,5,read,science-fiction\n'
        )
        upload = SimpleUploadedFile('goodreads.csv', csv_data.encode('utf-8'), 'text/csv')

        response = client.post('/api/goodreads/import/', {'file': upload}, format='multipart')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['imported'])
        self.assertEqual(response.data['profile']['imported_rows'], 1)

# Create your tests here.
