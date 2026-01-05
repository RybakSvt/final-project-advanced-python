from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import Booking, Availability
from apps.properties.models import RealEstateListing
from apps.shared.constants import MAX_BOOKING_DATE
from rest_framework import serializers
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    BookingUpdateSerializer,
    AvailabilitySerializer,
)
from apps.shared.permissions import IsHost



class BookingViewSet(viewsets.ModelViewSet):
    """
    API бронирований для гостей.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return BookingUpdateSerializer
        elif self.action == 'retrieve':
            return BookingDetailSerializer
        return BookingListSerializer

    def get_queryset(self):
        # Гость видит только свои бронирования
        return Booking.objects.filter(
            guest=self.request.user
        ).select_related(
            'listing__real_estate_object__address',
            'listing__real_estate_object__stats'
        ).prefetch_related('listing__real_estate_object__amenities')

    def perform_create(self, serializer):
        # Создаём бронирование с текущим пользователем как гость
        booking = serializer.save(guest=self.request.user)

        # Проверяем доступность
        available, message = booking.check_availability()
        if not available:
            raise serializers.ValidationError({'dates': message})

        # Бронирование остаётся в статусе 'pending' до подтверждения хоста
        booking.save()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена бронирования гостем"""
        booking = self.get_object()
        if booking.guest != request.user:
            return Response(
                {'error': 'You can only cancel your own bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        success, message = booking.cancel()
        if success:
            return Response({'status': 'cancelled', 'message': message})
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)



class HostBookingViewSet(viewsets.ModelViewSet):
    """
    API бронирований для хостов (управление бронированиями своих объявлений).
    """
    http_method_names = ['get', 'head', 'options', 'post'] # только confirm/reject
    permission_classes = [permissions.IsAuthenticated, IsHost]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookingDetailSerializer
        # Для list, create, update, partial_update, destroy
        return BookingListSerializer

    def get_queryset(self):
        return Booking.objects.filter(
            listing__real_estate_object__host=self.request.user
        ).select_related(
            'listing__real_estate_object__host__profile',
            'listing__real_estate_object__address',
            'guest__profile'
        ).prefetch_related('listing__real_estate_object__amenities')


        listing_id = self.request.query_params.get('listing')
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)

        status = self.request.query_params.get('status')
        if status in ['pending', 'confirmed', 'cancelled', 'completed']:
            queryset = queryset.filter(status=status)

        return queryset.order_by('check_in')

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Подтверждение бронирования хостом"""
        booking = self.get_object()
        success, message = booking.confirm()
        if success:
            return Response({'status': 'confirmed', 'message': message})
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Отклонение бронирования хостом"""
        booking = self.get_object()
        if booking.status != 'pending':
            return Response(
                {'error': 'Only pending bookings can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'cancelled'
        booking.save()
        return Response({'status': 'rejected', 'message': 'Booking rejected.'})


#  Управление доступностью (для хостов)
class AvailabilityViewSet(viewsets.ModelViewSet):
    """
    Управление периодами доступности для объявлений хоста.
    """
    permission_classes = [permissions.IsAuthenticated, IsHost]
    serializer_class = AvailabilitySerializer

    def get_queryset(self):
        return Availability.objects.filter(
            listing__real_estate_object__host=self.request.user
        ).select_related(
            'listing__real_estate_object__host__profile'  # ← для IsHost
        )


    def perform_create(self, serializer):
        # Проверяем, что объявление принадлежит хосту
        listing = serializer.validated_data['listing']
        if listing.real_estate_object.host != self.request.user:
            raise serializers.ValidationError(
                {'listing': 'You can only set availability for your own listings.'}
            )
        serializer.save()


class CalendarViewSet(viewsets.ViewSet):
    """
    Календарь доступности объявления.
    Доступен всем (гости, хосты, неавторизованные).
    GET /api/v1/calendar/{listing_id}/?month=1&year=2026
    """
    permission_classes = [permissions.AllowAny]

    def list(self, request, listing_id=None):
        # 1. Проверяем существование объявления
        try:
            listing = RealEstateListing.objects.get(
                id=listing_id,
                is_active=True,
                is_approved=True
            )
        except RealEstateListing.DoesNotExist:
            return Response(
                {'error': 'Listing not found or not available.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Получаем параметры месяца/года (по умолчанию текущий месяц)
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if month and year:
            try:
                start_date = timezone.datetime(int(year), int(month), 1).date()
            except ValueError:
                return Response(
                    {'error': 'Invalid month/year format.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Текущий месяц
            today = timezone.now().date()
            start_date = today.replace(day=1)

        # 3. Определяем диапазон (месяц)
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        end_date = min(end_date, MAX_BOOKING_DATE)  # не превышаем лимит

        # 4. Получаем доступные периоды
        availabilities = Availability.objects.filter(
            listing=listing,
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        # 5. Получаем бронирования
        bookings = Booking.objects.filter(
            listing=listing,
            status__in=['confirmed', 'pending'],
            check_in__lte=end_date,
            check_out__gte=start_date
        )

        # 6. Формируем календарь
        calendar = self._build_calendar(
            start_date, end_date,
            availabilities, bookings,
            listing.minimum_stay
        )

        return Response({
            'today': timezone.now().date().isoformat(),
            'listing_id': listing.id,
            'listing_title': listing.real_estate_object.title,
            'month': start_date.strftime('%Y-%m'),
            'currency': listing.currency,
            'price_per_night': str(listing.price_per_night),
            'minimum_stay': listing.minimum_stay,
            'calendar': calendar
        })

    def _build_calendar(self, start_date, end_date, availabilities, bookings, minimum_stay):
        """Строит массив дней с статусами"""
        calendar = []
        current_date = start_date

        while current_date <= end_date:
            # Проверяем доступность
            is_available = any(
                avail.start_date <= current_date <= avail.end_date
                for avail in availabilities
            )

            # Проверяем бронирования
            is_booked = any(
                booking.check_in <= current_date < booking.check_out
                for booking in bookings
            )

            # Определяем статус
            if is_booked:
                status = 'booked'
            elif not is_available:
                status = 'unavailable'
            else:
                # Проверяем минимальный срок бронирования
                status = 'available'
                # (можно добавить проверку, что от этой даты можно забронировать minimum_stay дней)

            calendar.append({
                'date': current_date.isoformat(),
                'status': status,
                'day_of_week': current_date.strftime('%A'),
                'is_weekend': current_date.weekday() >= 5  # суббота/воскресенье
            })

            current_date += timedelta(days=1)

        return calendar

    @action(detail=True, methods=['get'])
    def availability_range(self, request, listing_id=None):
        """Возвращает ближайшие доступные даты для бронирования"""
        listing = self.get_listing(listing_id)

        # Находим первый доступный период от сегодня
        today = timezone.now().date()
        availability = Availability.objects.filter(
            listing=listing,
            start_date__lte=today,
            end_date__gte=today
        ).first()

        if not availability:
            # Ищем следующий доступный период
            availability = Availability.objects.filter(
                listing=listing,
                start_date__gt=today
            ).order_by('start_date').first()

        if availability:
            return Response({
                'available_from': availability.start_date,
                'available_to': availability.end_date,
                'is_infinite': availability.is_infinite
            })

        return Response({
            'available_from': None,
            'available_to': None,
            'message': 'No availability found.'
        })