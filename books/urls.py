from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookViewSet,
    BookmarkViewSet,
    ChatView,
    GenreViewSet,
    GoodreadsImportView,
    RatingViewSet,
    RecommendView,
    StatsView,
)

router = DefaultRouter()
router.register('genres', GenreViewSet, basename='genre')
router.register('books', BookViewSet, basename='book')
router.register('bookmarks', BookmarkViewSet, basename='bookmark')
router.register('ratings', RatingViewSet, basename='rating')

urlpatterns = [
    path('chat/', ChatView.as_view(), name='chat'),
    path('goodreads/import/', GoodreadsImportView.as_view(), name='goodreads-import'),
    path('recommend/', RecommendView.as_view(), name='recommend'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('', include(router.urls)),
]
