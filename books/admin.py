from django.contrib import admin

from .models import Book, Bookmark, Genre, Rating, RecommendationLog


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'average_rating', 'published_year')
    list_filter = ('genres',)
    search_fields = ('title', 'author')
    filter_horizontal = ('genres',)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'updated_at')
    list_filter = ('status',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'score', 'updated_at')


admin.site.register(RecommendationLog)
