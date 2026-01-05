from rest_framework import serializers
from apps.reviews.models import PropertyReview


class ReviewPreviewSerializer(serializers.ModelSerializer):
    """Краткий отзыв для показа в карточке объявления"""
    guest_name = serializers.SerializerMethodField()
    guest_member_since = serializers.SerializerMethodField()

    class Meta:
        model = PropertyReview
        fields = ['id', 'rating', 'comment', 'created_at', 'guest_name', 'guest_member_since']

    def get_guest_name(self, obj):
        return f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username

    def get_guest_member_since(self, obj):
        return obj.guest.date_joined.year