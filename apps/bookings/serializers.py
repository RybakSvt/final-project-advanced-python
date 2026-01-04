from rest_framework import serializers
from django.utils import timezone
from .models import Booking, Availability
from apps.properties.serializers import ListingListSerializer, ListingReadSerializer  # для вложенного представления
from apps.users.serializers import UserPublicSerializer  # если есть
from apps.shared.constants import MAX_BOOKING_DATE


# 1. Создание бронирования (гость)
class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['listing', 'check_in', 'check_out']

    def validate(self, data):
        # Проверка дат
        if data['check_in'] >= data['check_out']:
            raise serializers.ValidationError(
                "Check-out date must be after check-in date"
            )

        # Проверка лимита времени
        if data['check_out'] > MAX_BOOKING_DATE:
            raise serializers.ValidationError(
                f"Booking cannot be later than {MAX_BOOKING_DATE}"
            )

        # Проверка, что даты в будущем
        if data['check_in'] <= timezone.now().date():
            raise serializers.ValidationError(
                "Check-in date must be in the future"
            )

        # Проверка доступности проводится в view
        return data

    def create(self, validated_data):
        validated_data['guest'] = self.context['request'].user
        return super().create(validated_data)


# 2. Список бронирований (гость/хост)
class BookingListSerializer(serializers.ModelSerializer):
    listing = ListingListSerializer(read_only=True)
    nights_count = serializers.IntegerField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'check_in', 'check_out',
            'nights_count', 'status', 'total_price', 'currency',
            'can_be_cancelled', 'created_at'
        ]


# 3. Детали бронирования (хост и гость)
class BookingDetailSerializer(serializers.ModelSerializer):
    listing = ListingReadSerializer(read_only=True)
    guest = serializers.SerializerMethodField()
    nights_count = serializers.IntegerField(read_only=True)
    cancellation_deadline = serializers.DateField(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = [
            'id', 'listing', 'price_per_night', 'currency',
            'total_price', 'created_at', 'updated_at'
        ]

    def get_guest(self, obj):
        request = self.context.get('request')
        # Показываем guest только если пользователь - хост этого объявления
        if request and request.user == obj.listing.real_estate_object.host:
            return UserPublicSerializer(obj.guest).data
        return None  # Для гостя вернёт null


# 4. Обновление статуса (хост/гость)
class BookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['status']

    def validate_status(self, value):
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['completed', 'cancelled'],
            'cancelled': [],
            'completed': []
        }

        current_status = self.instance.status
        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current_status} to {value}"
            )
        return value


# 5. Для управления доступностью (хост)
class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ['id', 'listing', 'start_date', 'end_date', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        # Для PATCH: берем недостающие поля из instance
        listing = data.get('listing', getattr(self.instance, 'listing', None))
        start_date = data.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = data.get('end_date', getattr(self.instance, 'end_date', None))

        # Базовые проверки
        if end_date and end_date > MAX_BOOKING_DATE:
            raise serializers.ValidationError("End date exceeds maximum booking date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")

        # Проверка пересечений
        if listing and start_date and end_date:
            queryset = Availability.objects.filter(
                listing=listing,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise serializers.ValidationError("Period overlaps with existing availability")

        return data


# 6. Календарь доступности
class BookingCalendarSerializer(serializers.Serializer):
    listing = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError(
                "Start date must be before end date"
            )
        if data['end_date'] > data['start_date'] + timezone.timedelta(days=365):
            raise serializers.ValidationError(
                "Date range cannot exceed 1 year"
            )
        return data