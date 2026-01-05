from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from apps.properties.views import BaseListingViewSet

from apps.properties.models import RealEstateListing
from apps.search.models import SearchHistory, ViewHistory, SearchKeyword
from .filters import ListingFilter
from .serializers import (
    SearchResultSerializer,
    SearchHistorySerializer,
    PopularKeywordSerializer,
    PopularListingSerializer
)

class SearchPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SearchViewSet(BaseListingViewSet):
    """
    Расширенный поиск с фильтрацией и сохранением истории
    """
    serializer_class = SearchResultSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = ListingFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['price_per_night', 'created_at', 'view_count']
    ordering = ['-created_at']
    pagination_class = SearchPagination

    def get_queryset(self):
        queryset = self.get_base_queryset()

        # annotate для рейтинга
        from django.db.models import Avg
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating')
        )

        # Фильтрация по доступности дат
        check_in = self.request.query_params.get('check_in')
        check_out = self.request.query_params.get('check_out')

        if check_in and check_out:
            from django.db.models import Q
            # Только доступные периоды
            queryset = queryset.filter(
                availabilities__start_date__lte=check_in,
                availabilities__end_date__gte=check_out
            ).exclude(
                Q(bookings__check_in__lt=check_out) &
                Q(bookings__check_out__gt=check_in) &
                Q(bookings__status__in=['confirmed', 'pending'])
            ).distinct()

        return queryset


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Сохранение истории поиска для авторизованных пользователей
        if request.user.is_authenticated:
            search_query = request.query_params.get('search', '')
            if search_query:
                SearchHistory.objects.create(
                    user=request.user,
                    query=search_query
                )

                # Обновление счетчика ключевых слов
                keyword, created = SearchKeyword.objects.get_or_create(
                    keyword=search_query.lower()
                )
                keyword.count += 1
                keyword.save()

        #Пагинация
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def popular_keywords(self, request):
        """Популярные поисковые запросы"""
        keywords = SearchKeyword.objects.all().order_by('-count')[:10]
        serializer = PopularKeywordSerializer(keywords, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def popular_listings(self, request):
        """Популярные объявления (по просмотрам)"""
        listings = RealEstateListing.objects.filter(
            is_active=True,
            is_approved=True,
            view_count__gt = 0
        ).order_by('-view_count')[:10]
        serializer = PopularListingSerializer(listings, many=True)
        return Response(serializer.data)
