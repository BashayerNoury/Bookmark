from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField()
    isbn = models.CharField(max_length=20, blank=True)
    cover_color = models.CharField(max_length=7, default='#4A6FA5')
    cover_url = models.URLField(blank=True)
    published_year = models.PositiveIntegerField(null=True, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    ratings_count = models.PositiveIntegerField(default=0)
    genres = models.ManyToManyField(Genre, related_name='books', blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-average_rating', 'title']

    def __str__(self):
        return f'{self.title} — {self.author}'


class Bookmark(models.Model):
    STATUS_WANT = 'want'
    STATUS_READING = 'reading'
    STATUS_FINISHED = 'finished'
    STATUS_CHOICES = [
        (STATUS_WANT, 'Want to read'),
        (STATUS_READING, 'Reading'),
        (STATUS_FINISHED, 'Finished'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bookmarks')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_WANT)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.username} → {self.book.title}'


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='ratings')
    score = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.username} rated {self.book.title}: {self.score}'


class RecommendationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_logs', null=True, blank=True)
    query = models.TextField(blank=True)
    mood = models.CharField(max_length=128, blank=True)
    result_ids = models.JSONField(default=list)
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class GoodreadsTasteProfile(models.Model):
    """A compact, account-owned summary of a Goodreads Library Export."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goodreads_taste',
    )
    favorite_authors = models.JSONField(default=list, blank=True)
    favorite_shelves = models.JSONField(default=list, blank=True)
    liked_books = models.JSONField(default=list, blank=True)
    disliked_books = models.JSONField(default=list, blank=True)
    reading_history = models.JSONField(default=list, blank=True)
    rating_summary = models.JSONField(default=dict, blank=True)
    imported_rows = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} Goodreads taste'


class GoodreadsImport(models.Model):
    """Audit metadata only: the uploaded CSV itself is never retained."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goodreads_imports',
    )
    filename = models.CharField(max_length=255)
    imported_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
