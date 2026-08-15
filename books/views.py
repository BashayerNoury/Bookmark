from django_filters import rest_framework as filters
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .chat import chat_reply
from .goodreads_import import parse_goodreads_csv
from .models import Book, Bookmark, Genre, GoodreadsImport, GoodreadsTasteProfile, Rating
from .recommendations import recommend_books
from .serializers import (
    BookDetailSerializer,
    BookListSerializer,
    BookmarkSerializer,
    ChatRequestSerializer,
    GenreSerializer,
    GoodreadsTasteProfileSerializer,
    RatingSerializer,
    RecommendRequestSerializer,
)


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class BookFilter(filters.FilterSet):
    genre = filters.CharFilter(field_name='genres__slug')
    author = filters.CharFilter(field_name='author', lookup_expr='icontains')
    min_rating = filters.NumberFilter(field_name='average_rating', lookup_expr='gte')

    class Meta:
        model = Book
        fields = ['genre', 'author', 'min_rating']


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.prefetch_related('genres').all()
    permission_classes = [permissions.AllowAny]
    filterset_class = BookFilter
    search_fields = ['title', 'author', 'description', 'tags']
    ordering_fields = ['average_rating', 'published_year', 'title', 'created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookDetailSerializer
        return BookListSerializer


class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related('book').prefetch_related('book__genres')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle(self, request):
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'detail': 'book_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)

        existing = Bookmark.objects.filter(user=request.user, book=book).first()
        if existing:
            existing.delete()
            return Response({'bookmarked': False, 'book_id': book.id})

        bm = Bookmark.objects.create(user=request.user, book=book)
        return Response({'bookmarked': True, 'bookmark': BookmarkSerializer(bm, context={'request': request}).data})


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user).select_related('book')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RecommendView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        books, explanation = recommend_books(
            user=request.user if request.user.is_authenticated else None,
            query=data.get('query', ''),
            mood=data.get('mood', ''),
            limit=data.get('limit', 6),
        )
        return Response({
            'explanation': explanation,
            'books': BookListSerializer(books, many=True, context={'request': request}).data,
        })


class StatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        payload = {
            'books': Book.objects.count(),
            'genres': Genre.objects.count(),
        }
        if request.user.is_authenticated:
            payload['bookmarks'] = Bookmark.objects.filter(user=request.user).count()
            payload['ratings'] = Rating.objects.filter(user=request.user).count()
        return Response(payload)


class ChatView(APIView):
    """ChatGPT-style conversational book recommendations (Gemini + Open Library)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = chat_reply(
            message=data['message'],
            history=data.get('history') or [],
            user=request.user if request.user.is_authenticated else None,
            limit=data.get('limit', 4),
        )
        return Response({
            'reply': result['reply'],
            'books': result.get('books') or [],
        })


class GoodreadsImportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = GoodreadsTasteProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({'imported': False})
        return Response({
            'imported': True,
            'profile': GoodreadsTasteProfileSerializer(profile).data,
        })

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'detail': 'Choose your Goodreads Library Export CSV first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            parsed = parse_goodreads_csv(uploaded_file)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = GoodreadsTasteProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'favorite_authors': parsed['favorite_authors'],
                'favorite_shelves': parsed['favorite_shelves'],
                'liked_books': parsed['liked_books'],
                'disliked_books': parsed['disliked_books'],
                'reading_history': parsed['reading_history'],
                'rating_summary': parsed['rating_summary'],
                'imported_rows': parsed['valid_rows'],
            },
        )
        GoodreadsImport.objects.create(
            user=request.user,
            filename=uploaded_file.name[:255],
            imported_rows=parsed['total_rows'],
            valid_rows=parsed['valid_rows'],
        )
        return Response({
            'imported': True,
            'profile': GoodreadsTasteProfileSerializer(profile).data,
            'summary': {
                'books_imported': parsed['valid_rows'],
                'top_authors': [item['name'] for item in parsed['favorite_authors'][:3]],
                'top_shelves': [item['name'] for item in parsed['favorite_shelves'][:3]],
            },
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        GoodreadsTasteProfile.objects.filter(user=request.user).delete()
        GoodreadsImport.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

