from rest_framework import serializers
from apps.properties.serializers import ListingListSerializer
from apps.search.models import SearchKeyword, SearchHistory


class SearchResultSerializer(ListingListSerializer):
    """Расширенный сериализатор для поиска с дополнительными полями"""
    avg_rating = serializers.FloatField()
    review_count = serializers.SerializerMethodField()

    class Meta(ListingListSerializer.Meta):
        fields = ListingListSerializer.Meta.fields + ['avg_rating', 'review_count']

    def get_review_count(self, obj):
        return obj.reviews.count()


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ['id', 'query', 'created_at']
        read_only_fields = ['id', 'created_at']


class PopularKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchKeyword
        fields = ['keyword', 'count']


class PopularListingSerializer(ListingListSerializer):
    """Сериализатор для популярных объявлений"""

    class Meta(ListingListSerializer.Meta):
        fields = ListingListSerializer.Meta.fields