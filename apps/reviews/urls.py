from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PropertyReviewViewSet,
    UserRatingViewSet,
    ListingReviewsViewSet
)

router = DefaultRouter()
router.register('property-reviews', PropertyReviewViewSet, basename='property-review')
router.register('user-ratings', UserRatingViewSet, basename='user-rating')

# Отдельный роутер для публичных отзывов по объявлению
listing_reviews_list = ListingReviewsViewSet.as_view({'get': 'list'})

urlpatterns = [
    path('', include(router.urls)),
    path('listings/<int:listing_id>/reviews/', listing_reviews_list, name='listing-reviews'),
]