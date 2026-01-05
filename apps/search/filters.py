from django_filters import rest_framework as filters
from apps.properties.models import RealEstateListing
from django.db.models import Q

from apps.shared.constants import PROPERTY_TYPES


class ListingFilter(filters.FilterSet):
    # Цена
    min_price = filters.NumberFilter(field_name='price_per_night', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price_per_night', lookup_expr='lte')

    # Количество комнат
    min_rooms = filters.NumberFilter(field_name='real_estate_object__stats__rooms', lookup_expr='gte')
    max_rooms = filters.NumberFilter(field_name='real_estate_object__stats__rooms', lookup_expr='lte')

    # Город
    city = filters.CharFilter(field_name='real_estate_object__address__city', lookup_expr='icontains')

    property_type = filters.ChoiceFilter(
        field_name='real_estate_object__property_type',
        choices=PROPERTY_TYPES     # импорт из constants.py
    )

    # Доступность по датам
    check_in = filters.DateFilter(
        field_name='availabilities__start_date',
        lookup_expr='lte',
        label='Available from (check-in date)'
    )
    check_out = filters.DateFilter(
        field_name='availabilities__end_date',
        lookup_expr='gte',
        label='Available until (check-out date)'
    )

    # Поиск по ключевым словам
    search = filters.CharFilter(
        method='filter_search',
        label='Search in title/description'
    )

    class Meta:
        model = RealEstateListing
        fields = [
            'min_price', 'max_price',
            'min_rooms', 'max_rooms',
            'city', 'property_type',
            'check_in', 'check_out',
            'search', #'ordering',
        ]


    def filter_search(self, queryset, name, value):
        """Поиск по ключевым словам в заголовке и описании"""
        if value:
            return queryset.filter(
                Q(real_estate_object__title__icontains=value) |
                Q(real_estate_object__description__icontains=value) |
                Q(promo_title__icontains=value)
            )
        return queryset