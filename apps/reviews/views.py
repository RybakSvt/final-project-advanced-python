from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .models import PropertyReview, UserRating
from apps.reviews.serializers import (
    PropertyReviewSerializer,
    UserRatingSerializer,
    PropertyReviewPublicSerializer
)
from apps.shared.permissions import IsReviewParticipant

class PropertyReviewViewSet(viewsets.ModelViewSet):
    """
        ViewSet для отзывов на объявления.
        Гость может создавать/редактировать свои отзывы.
        """
    serializer_class = PropertyReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewParticipant]  # ← ИЗМЕНЕНИЕ
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        user = self.request.user

        # Хост видит все отзывы на свои объявления
        if hasattr(user, 'profile') and user.profile.roles.filter(name='host').exists():
            return PropertyReview.objects.filter(
                listing__real_estate_object__host=user
            ).select_related(
                'guest', 'listing', 'booking'
            ).order_by('-created_at')

        # Гость видит только свои отзывы
        return PropertyReview.objects.filter(
            guest=user
        ).select_related(
            'guest', 'listing', 'booking'
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list' and not self.request.user.is_staff:
            # Для списка используем публичный сериализатор
            return PropertyReviewPublicSerializer
        return PropertyReviewSerializer

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Отзывы, оставленные текущим пользователем"""
        reviews = PropertyReview.objects.filter(
            guest=request.user
        ).select_related('listing').order_by('-created_at')

        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def for_my_listings(self, request):
        """Отзывы на объявления текущего хоста"""
        if not hasattr(request.user, 'profile') or not request.user.profile.roles.filter(name='host').exists():
            return Response(
                {'error': 'You are not a host'},
                status=status.HTTP_403_FORBIDDEN
            )

        reviews = PropertyReview.objects.filter(
            listing__real_estate_object__host=request.user,
            is_approved=True  # показываем только одобренные
        ).select_related('guest', 'listing').order_by('-created_at')

        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = PropertyReviewPublicSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = PropertyReviewPublicSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)

class UserRatingViewSet(viewsets.ModelViewSet):
    """
        ViewSet для рейтингов пользователей.
        Участники бронирования могут оценивать друг друга.
        """
    serializer_class = UserRatingSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewParticipant]  # ← ИЗМЕНЕНИЕ
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        user = self.request.user

        # Пользователь видит оценки, которые он получил или поставил
        return UserRating.objects.filter(
            Q(rated_user=user) | Q(rating_user=user)
        ).select_related(
            'rated_user', 'rating_user', 'booking__listing__real_estate_object'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(rating_user=self.request.user)

    @action(detail=False, methods=['get'])
    def received(self, request):
        """Оценки, полученные текущим пользователем"""
        ratings = UserRating.objects.filter(
            rated_user=request.user
        ).select_related('rating_user', 'booking').order_by('-created_at')

        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def given(self, request):
        """Оценки, поставленные текущим пользователем"""
        ratings = UserRating.objects.filter(
            rating_user=request.user
        ).select_related('rated_user', 'booking').order_by('-created_at')

        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Бронирования, которые можно оценить"""
        from apps.bookings.models import Booking

        # Бронирования, где пользователь участник и бронирование завершено
        bookings = Booking.objects.filter(
            Q(guest=request.user) | Q(listing__real_estate_object__host=request.user),
            status='completed',
            check_out__lte=timezone.now().date() - timezone.timedelta(days=1)  # прошел хотя бы 1 день после выезда
        ).exclude(
            # Исключаются уже оцененные
            Q(user_ratings__rating_user=request.user) | Q(user_ratings__rated_user=request.user)
        ).select_related(
            'listing__real_estate_object',
            'guest'
        ).distinct()

        result = []
        for booking in bookings:
            if request.user == booking.guest:
                rate_user = booking.listing.real_estate_object.host
                relation = 'host'
            else:
                rate_user = booking.guest
                relation = 'guest'

            result.append({
                'booking_id': booking.id,
                'check_in': booking.check_in,
                'check_out': booking.check_out,
                'listing_title': booking.listing.real_estate_object.title,
                'user_to_rate': {
                    'id': rate_user.id,
                    'name': f"{rate_user.first_name} {rate_user.last_name}".strip() or rate_user.username,
                    'relation': relation
                }
            })

        return Response(result)


class ListingReviewsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Публичные отзывы на конкретное объявление.
    Доступны всем, показываются только одобренные отзывы.
    """
    serializer_class = PropertyReviewPublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        listing_id = self.kwargs.get('listing_id')
        return PropertyReview.objects.filter(
            listing_id=listing_id,
            is_approved=True
        ).select_related('guest').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Пагинация
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)