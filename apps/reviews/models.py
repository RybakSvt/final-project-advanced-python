from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.shared.constants import RATING_CATEGORIES, RATING_VALUES


class PropertyReview(models.Model):
    """
    Отзыв на объявление.
    Один отзыв на одно завершенное бронирование.
    """
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='property_review',
        verbose_name=_('Booking'),
        help_text=_('The booking this review is for')
    )

    guest = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='property_reviews_given',
        verbose_name=_('Guest'),
        help_text=_('Guest who left the review')
    )

    listing = models.ForeignKey(
        'properties.RealEstateListing',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Listing')
    )

    rating = models.PositiveSmallIntegerField(
        verbose_name=_('Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1 to 5 stars')
    )

    comment = models.TextField(
        verbose_name=_('Comment'),
        max_length=1000,
        blank=True,
        help_text=_('Detailed review comment')
    )

    # Модерация
    is_approved = models.BooleanField(
        default=False,
        help_text=_('Review is hidden until moderator approves')
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
        verbose_name = _('Property Review')
        verbose_name_plural = _('Property Reviews')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['listing', 'created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['booking'],
                name='unique_review_per_booking'
            ),
        ]

    def __str__(self):
        return f"Review #{self.id}: {self.rating} for {self.listing}"


    def save(self, *args, **kwargs):
        # Автоматически устанавливаем guest и listing из booking
        if self.booking_id and not self.guest_id:
            self.guest = self.booking.guest  # ← может падать здесь
        if self.booking_id and not self.listing_id:
            self.listing = self.booking.listing  # ← и здесь

        # Проверка, что booking существует и имеет связи
        if not hasattr(self, 'booking') or self.booking is None:
            raise ValueError("Cannot save PropertyReview without booking")

        super().save(*args, **kwargs)


class UserRating(models.Model):
    """
    Рейтинг пользователя по трём критериям за одно бронирование.
    Одна запись содержит все три оценки.
    """
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='user_ratings',
        verbose_name=_('Booking'),
        help_text=_('Booking this rating is for')
    )

    rating_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='given_ratings',
        verbose_name=_('Rating User'),
        help_text=_('User giving the rating')
    )

    rated_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='received_ratings',
        verbose_name=_('Rated User'),
        help_text=_('User being rated')
    )

    # Три оценки вместо одной категории
    satisfaction = models.CharField(
        verbose_name=_('Satisfaction'),
        max_length=10,
        choices=RATING_VALUES,
        default='OK',
        help_text=_('Satisfaction rating (TOP/OK/POOR)')
    )

    friendliness = models.CharField(
        verbose_name=_('Friendliness'),
        max_length=10,
        choices=RATING_VALUES,
        default='OK',
        help_text=_('Friendliness rating (TOP/OK/POOR)')
    )

    reliability = models.CharField(
        verbose_name=_('Reliability'),
        max_length=10,
        choices=RATING_VALUES,
        default='OK',
        help_text=_('Reliability rating (TOP/OK/POOR)')
    )

    comment = models.TextField(
        verbose_name=_('Comment'),
        blank=True,
        help_text=_('Optional explanation for the rating')
    )

    created_at = models.DateTimeField(
        verbose_name=_('Created At'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('User Rating')
        verbose_name_plural = _('User Ratings')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['booking', 'rating_user', 'rated_user'],
                name='unique_rating_per_booking_pair'
            ),
        ]

    def __str__(self):
        return f"{self.rating_user} -> {self.rated_user} (S:{self.satisfaction}, F:{self.friendliness}, R:{self.reliability})"

    def save(self, *args, **kwargs):
        """Автоматически определяет rated_user если не задан"""
        if not self.rated_user_id and self.booking:
            if self.rating_user == self.booking.guest:
                self.rated_user = self.booking.listing.real_estate_object.host
            else:
                self.rated_user = self.booking.guest
        super().save(*args, **kwargs)

    @property
    def scores(self):
        """Возвращает словарь с числовыми значениями оценок"""
        score_map = {'TOP': 100, 'OK': 50, 'POOR': 0}
        return {
            'satisfaction': score_map.get(self.satisfaction, 0),
            'friendliness': score_map.get(self.friendliness, 0),
            'reliability': score_map.get(self.reliability, 0),
        }