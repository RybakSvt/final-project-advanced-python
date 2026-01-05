from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Avg, Count


from .models import RealEstateObject, RealEstateListing
from .serializers import (
    RealEstateObjectListSerializer,
    RealEstateObjectReadSerializer,
    RealEstateObjectWriteSerializer,
    ListingListSerializer,
    ListingReadSerializer,
    ListingHostDetailSerializer,
    ListingWriteSerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from ..shared.permissions import IsHost


#          === БАЗОВЫЙ КЛАСС ===
class BaseListingViewSet(viewsets.ReadOnlyModelViewSet):
    """Базовый ViewSet для объявлений с общим queryset."""

    def get_base_queryset(self):
        queryset = RealEstateListing.objects.filter(
            is_active=True,
            is_approved=True
        ).select_related(
            'real_estate_object__address',
            'real_estate_object__stats',
            'real_estate_object__host'
        ).prefetch_related(
            'real_estate_object__amenities',
            'reviews'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            total_reviews=Count('reviews')
        )
        return queryset


class RealEstateObjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для объектов недвижимости.
    Хост видит только свои объекты.
    """
#    permission_classes = [permissions.IsAuthenticated, IsHost]
    #http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        return RealEstateObject.objects.filter(
            host=self.request.user
        ).select_related(
            'host__profile'
        ).prefetch_related(
            'amenities'
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return RealEstateObjectListSerializer
        if self.action == 'retrieve':
            return RealEstateObjectReadSerializer
        return RealEstateObjectWriteSerializer

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class PublicListingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Публичный API списка объявлений (для гостей и хостов как гостей)
    """
    serializer_class = ListingListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['real_estate_object__address__city', 'price_per_night', 'real_estate_object__property_type']
    ordering_fields = ['price_per_night', 'created_at']
    ordering = ['-created_at']         # новые первыми

    def get_queryset(self):
        queryset = RealEstateListing.objects.filter(
            is_active=True,
            is_approved=True
        ).select_related(
            'real_estate_object__address',
            'real_estate_object__stats'
        ).prefetch_related('real_estate_object__amenities')

        # Дополнительные фильтры из параметров запроса
        # (например, по датам availability)
        return queryset


class ListingDetailViewSet(BaseListingViewSet):
    """
    Детальный просмотр объявления (публичный для всех)
    GET /api/v1/listing/{id}/
    """
    serializer_class = ListingReadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return self.get_base_queryset()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_authenticated:
            from apps.search.models import ViewHistory
            ViewHistory.objects.create(user=request.user, listing=instance)
        return super().retrieve(request, *args, **kwargs)


class HostListingViewSet(viewsets.ModelViewSet):
    """Управление объявлениями для хоста"""
    permission_classes = [permissions.IsAuthenticated, IsHost]


    def get_serializer_class(self):
        if self.action == 'list':
            return ListingListSerializer
        elif self.action == 'retrieve':
            return ListingHostDetailSerializer
        return ListingWriteSerializer

    def get_queryset(self):
        return RealEstateListing.objects.filter(
            real_estate_object__host=self.request.user
        ).select_related(
            'real_estate_object__host__profile',  # ← ДОБАВИТЬ для IsHost
            'real_estate_object__address',
            'real_estate_object__stats'
        ).prefetch_related(
            'real_estate_object__amenities',
            'reviews',
            # '.images' после добавления
        )

    def perform_create(self, serializer):
        serializer.save()  # валидация принадлежности есть в сериализаторе

    # @action(detail=True, methods=['post'], permission_classes=[IsHost])
    # def upload_photos(self, request, pk=None):
    #     """Отдельный эндпоинт для загрузки фото"""
    #     listing = self.get_object()
    #     # Обработка загрузки фото
    #     return Response({'status': 'photos uploaded'})