from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from apps.shared.constants import BOOKING_STATUS_CHOICES, CURRENCY_CHOICES, INFINITE_DATE


class Availability(models.Model):
    """
    Доступные периоды для бронирования.
    Host задает периоды, когда объект доступен.
    end_date = INFINITE_DATE означает бесконечный период.
    """
    listing = models.ForeignKey(
        'properties.RealEstateListing',
        on_delete=models.CASCADE,
        related_name='availabilities',
        verbose_name=_('Listing')
    )

    start_date = models.DateField(                   # бронирование считается по дням, а не по минутам
        verbose_name=_('Start Date'),
        help_text=_('First available date')
    )

    end_date = models.DateField(
        verbose_name=_('End Date'),
        default=INFINITE_DATE,
        help_text=_('Last available date (defaults to far future for open-ended availability)')
    )

    created_at = models.DateTimeField(
        verbose_name=_('Created At'),
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        verbose_name=_('Updated At'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('Availability')
        verbose_name_plural = _('Availabilities')
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['listing', 'start_date']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F('start_date')),
                name='end_date_after_start_date'
            ),
        ]

    def __str__(self):
        if self.is_infinite:
            return f"{self.start_date} and later for {self.listing}"
        return f"{self.start_date} - {self.end_date} for {self.listing}"

    @property
    def is_infinite(self):
        """Является ли период бесконечным (до 2999-12-31)"""
        return self.end_date == INFINITE_DATE

    @property
    def display_end_date(self):
        """Отображаемая дата окончания """
        if self.is_infinite:
            return None
        return self.end_date

    def is_date_in_range(self, check_date):
        """Проверяет, входит ли дата в период"""
        return self.start_date <= check_date <= self.end_date

    def covers_period(self, start_date, end_date):
        """Покрывает ли период указанные даты"""
        return (self.start_date <= start_date and
                end_date <= self.end_date)


class Booking(models.Model):
    """
    Бронирование (создание, отмена, подтверждение бронирования).
    """

    listing = models.ForeignKey(
        'properties.RealEstateListing',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('Listing')
    )

    guest = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('Guest')
    )


    check_in = models.DateField(
        verbose_name=_('Check-in Date')
    )

    check_out = models.DateField(
        verbose_name=_('Check-out Date')
    )

    # Цена фиксируется на момент создания
    price_per_night = models.DecimalField(
        verbose_name=_('Price Per Night'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    currency = models.CharField(
        verbose_name=_('Currency'),
        max_length=3,
        default='EUR',
        choices=CURRENCY_CHOICES
    )

    total_price = models.DecimalField(
        verbose_name=_('Total Price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Статус (pending → confirmed → completed/cancelled)
    status = models.CharField(
        verbose_name=_('Status'),
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default='pending'
    )

    # Отмена до определенной даты"
    cancellation_deadline = models.DateField(
        verbose_name=_('Cancellation Deadline'),
        help_text=_('Last date to cancel this booking for free')
    )


    created_at = models.DateTimeField(
        verbose_name=_('Created At'),
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        verbose_name=_('Updated At'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['guest', 'status']),                # пересмотреть
            models.Index(fields=['listing', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(check_out__gt=models.F('check_in')),
                name='check_out_after_check_in'
            ),
        ]

    def __str__(self):
        return f"Booking #{self.id}: {self.guest} → {self.listing} ({self.status})"

    def save(self, *args, **kwargs):
        """Автоматический расчет при сохранении"""
        is_new = self.pk is None

        # Устанавливаем цену из Listing, если не задана (только для новых)
        if is_new and not self.price_per_night and self.listing:
            self.price_per_night = self.listing.price_per_night
            self.currency = self.listing.currency

        # Рассчитываем общую цену
        if self.price_per_night and self.nights_count > 0:
            self.total_price = self.price_per_night * Decimal(self.nights_count)

        # Устанавливаем дедлайн отмены
        if not self.cancellation_deadline and self.listing and self.check_in:
            self.cancellation_deadline = self.check_in - timezone.timedelta(
                days=self.listing.cancellation_days_before
            )

        super().save(*args, **kwargs)

    @property
    def nights_count(self):
        """Количество ночей"""
        if self.check_in and self.check_out:
            return (self.check_out - self.check_in).days
        return 0

    @property
    def can_be_cancelled(self):
        """Можно ли отменить бронирование  до определенной даты)"""
        if self.status not in ['pending', 'confirmed']:
            return False

        return timezone.now().date() <= self.cancellation_deadline

    @property
    def is_upcoming(self):
        """Предстоящее ли бронирование"""
        return self.status == 'confirmed' and self.check_in > timezone.now().date()

    @property
    def is_active(self):
        """Активное ли бронирование (гость сейчас проживает)"""
        today = timezone.now().date()
        return (self.status == 'confirmed' and
                self.check_in <= today <= self.check_out)

    def check_availability(self):
        """Проверяет, доступны ли выбранные даты"""
        if not self.check_in or not self.check_out:
            return False, "Dates not specified"

        # Проверка минимального срока
        if self.nights_count < self.listing.minimum_stay:
            return False, f"Minimum stay is {self.listing.minimum_stay} nights"

        # Проверка дат (не в прошлом)
        if self.check_in <= timezone.now().date():
            return False, "Check-in date must be in the future"

        # Проверка доступности периода
        availability = self.listing.availabilities.filter(
            start_date__lte=self.check_in,
            end_date__gte=self.check_out
        ).first()

        if not availability:
            return False, "Selected dates are not available"

        return True, "Available"

    def confirm(self):
        """Подтвердить бронирование в транзакции (подтверждение хостером)"""
        if self.status != 'pending':
            return False, "Booking is not pending"

        available, message = self.check_availability()
        if not available:
            return False, message

        try:
            with transaction.atomic():
                # Блокируем запись для предотвращения race condition
                availability = self.listing.availabilities.filter(
                    start_date__lte=self.check_in,
                    end_date__gte=self.check_out
                ).select_for_update().first()

                if not availability:
                    return False, "Dates are no longer available"

                # Разделяем период доступности
                periods_to_create = []

                # Период ДО брони (если бронь не начинается в start_date)
                if availability.start_date < self.check_in:
                    periods_to_create.append(
                        Availability(
                            listing=self.listing,
                            start_date=availability.start_date,
                            end_date=self.check_in - timezone.timedelta(days=1)
                        )
                    )

                # Период ПОСЛЕ брони (если бронь не заканчивается в end_date)
                if availability.end_date > self.check_out:
                    periods_to_create.append(
                        Availability(
                            listing=self.listing,
                            start_date=self.check_out + timezone.timedelta(days=1),
                            end_date=availability.end_date
                        )
                    )

                # Удаляем старый период и создаем новые
                availability.delete()
                if periods_to_create:
                    Availability.objects.bulk_create(periods_to_create)

                # Отклоняем пересекающиеся pending брони
                Booking.objects.filter(
                    listing=self.listing,
                    status='pending',
                    check_in__lt=self.check_out,
                    check_out__gt=self.check_in
                ).exclude(id=self.id).update(status='cancelled')

                # Подтверждаем текущую бронь
                self.status = 'confirmed'
                super().save(update_fields=['status', 'updated_at'])

                return True, "Booking confirmed successfully"

        except Exception as e:
            # При любой ошибке транзакция откатывается
            return False, f"Error confirming booking: {str(e)}"

    def cancel(self):
        """Отменить бронирование (гостем/хостером)"""
        if self.status not in ['pending', 'confirmed']:
            return False, "Cannot cancel booking in current status"

        old_status = self.status
        self.status = 'cancelled'
        self.save()

        # Возвращаем даты в доступность только если бронь была confirmed
        if old_status == 'confirmed':
            with transaction.atomic():
                Availability.objects.create(
                    listing=self.listing,
                    start_date=self.check_in,
                    end_date=self.check_out - timezone.timedelta(days=1)
                )

        return True, "Booking cancelled"

    def complete(self):
        """Завершить бронирование (после выезда)"""
        if self.status == 'confirmed' and self.check_out < timezone.now().date():
            self.status = 'completed'
            self.save()
            return True, "Booking completed"
        return False, "Cannot complete booking"