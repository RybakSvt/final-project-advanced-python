from django.contrib import admin
from .models import UserRating, PropertyReview

@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'rating_user', 'rated_user', 'category', 'rating', 'created_at')
    list_filter = ('category', 'rating', 'created_at')
    search_fields = ('rating_user__username', 'rated_user__username', 'comment')
    readonly_fields = ('created_at',)

@admin.register(PropertyReview)
class PropertyReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'listing', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('guest__username', 'listing__title', 'comment')
    readonly_fields = ('created_at', 'updated_at')

