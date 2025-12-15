from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


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
        """Автоматически устанавливаем guest и listing из booking"""
        if self.booking and not self.guest:
            self.guest = self.booking.guest
        if self.booking and not self.listing:
            self.listing = self.booking.listing
        super().save(*args, **kwargs)


class UserRating(models.Model):
    """
    Рейтинг пользователя по категориям (TOP/OK/POOR).
    Используется для satisfaction, friendliness, reliability.
    """
    RATING_CATEGORIES = [
        ('satisfaction', _('Satisfaction')),
        ('friendliness', _('Friendliness')),
        ('reliability', _('Reliability')),
    ]

    RATING_VALUES = [
        ('TOP', _('TOP')),
        ('OK', _('OK')),
        ('POOR', _('POOR')),
    ]

    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='user_ratings',
        verbose_name=_('Booking'),
        help_text=_('Booking this rating is for')
    )

    rated_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='received_ratings',
        verbose_name=_('Rated User'),
        help_text=_('User being rated')
    )

    rating_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='given_ratings',
        verbose_name=_('Rating User'),
        help_text=_('User giving the rating')
    )

    category = models.CharField(
        verbose_name=_('Category'),
        max_length=20,
        choices=RATING_CATEGORIES,
        help_text=_('Rating category')
    )

    rating = models.CharField(
        verbose_name=_('Rating'),
        max_length=10,
        choices=RATING_VALUES,
        help_text=_('Rating value (TOP/OK/POOR)')
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
        indexes = [
            models.Index(fields=['rated_user', 'category']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['rated_user', 'rating_user', 'category', 'booking'],
                name='unique_rating_per_category_booking'
            ),
        ]

    def __str__(self):
        return f"{self.rating_user} -> {self.rated_user}: {self.category} - {self.rating}"

    @property
    def score_value(self):
        """Преобразует TOP/OK/POOR в числовое значение"""
        scores = {'TOP': 100, 'OK': 50, 'POOR': 0}
        return scores.get(self.rating, 0)