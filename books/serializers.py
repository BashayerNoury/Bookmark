from django.db.models import Avg
from rest_framework import serializers

from .models import Book, Bookmark, Genre, Rating


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name', 'slug')


class BookListSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            'id', 'title', 'author', 'description', 'cover_color',
            'published_year', 'page_count', 'average_rating', 'ratings_count',
            'genres', 'tags', 'is_bookmarked',
        )

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarks.filter(user=request.user).exists()


class BookDetailSerializer(BookListSerializer):
    user_rating = serializers.SerializerMethodField()
    bookmark_status = serializers.SerializerMethodField()

    class Meta(BookListSerializer.Meta):
        fields = BookListSerializer.Meta.fields + ('isbn', 'user_rating', 'bookmark_status')

    def get_user_rating(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        rating = obj.ratings.filter(user=request.user).first()
        if not rating:
            return None
        return {'score': rating.score, 'review': rating.review}

    def get_bookmark_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        bm = obj.bookmarks.filter(user=request.user).first()
        return bm.status if bm else None


class BookmarkSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source='book', write_only=True
    )

    class Meta:
        model = Bookmark
        fields = ('id', 'book', 'book_id', 'status', 'notes', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class RatingSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = Rating
        fields = ('id', 'book', 'book_title', 'score', 'review', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    def validate_score(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Score must be between 1 and 5.')
        return value

    def create(self, validated_data):
        rating, _ = Rating.objects.update_or_create(
            user=self.context['request'].user,
            book=validated_data['book'],
            defaults={
                'score': validated_data['score'],
                'review': validated_data.get('review', ''),
            },
        )
        self._refresh_book_rating(rating.book)
        return rating

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._refresh_book_rating(instance.book)
        return instance

    @staticmethod
    def _refresh_book_rating(book):
        agg = book.ratings.aggregate(avg=Avg('score'))
        book.average_rating = round(agg['avg'] or 0, 2)
        book.ratings_count = book.ratings.count()
        book.save(update_fields=['average_rating', 'ratings_count'])


class RecommendRequestSerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True, max_length=500)
    mood = serializers.CharField(required=False, allow_blank=True, max_length=128)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=6)


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'assistant'])
    content = serializers.CharField(max_length=4000)


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    history = ChatMessageSerializer(many=True, required=False, default=list)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=8, default=4)
