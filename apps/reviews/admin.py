from django.contrib import admin
from .models import PropertyReview, UserRating

@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'booking', 'rating_user', 'rated_user',
        'satisfaction', 'friendliness', 'reliability', 'created_at'
    ]
    list_filter = [
        'satisfaction', 'friendliness', 'reliability',
        'created_at'
    ]
    search_fields = [
        'rating_user__username', 'rated_user__username',
        'booking__id', 'comment'
    ]
    raw_id_fields = ['booking', 'rating_user', 'rated_user']

@admin.register(PropertyReview)
class PropertyReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'listing', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('guest__username', 'listing__title', 'comment')
    readonly_fields = ('created_at', 'updated_at')

