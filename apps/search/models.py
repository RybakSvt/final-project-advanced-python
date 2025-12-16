from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from django.utils import timezone



class SearchKeyword(models.Model):
    keyword = models.CharField(max_length=255, unique=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('Search Keyword')
        verbose_name_plural = _('Search Keywords')
        ordering = ['-count']

    def __str__(self):
        return f"{self.keyword} ({self.count})"


class SearchHistory(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='search_history'
    )
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Search History')
        verbose_name_plural = _('Search Histories')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user}: {self.query}"


class ViewHistory(models.Model):
    """
    Детальная история. Кто, когда, что смотрел.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='view_history'
    )
    listing = models.ForeignKey(
        'properties.RealEstateListing',
        on_delete=models.CASCADE,
        related_name='view_history'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['listing', 'viewed_at']),
            models.Index(fields=['user', 'listing']),
        ]
        verbose_name = _('View History')
        verbose_name_plural = _('View Histories')

    def save(self, *args, **kwargs):
        #  Проверка хоста
        if self.user == self.listing.real_estate_object.host:
            return

        #  Проверка уникальности
        today = self.viewed_at.date() if self.viewed_at else timezone.now().date()
        if ViewHistory.objects.filter(
                user=self.user,
                listing=self.listing,
                viewed_at__date=today
        ).exists():
            return

        super().save(*args, **kwargs)

        #  Увеличить счётчик, если поле существует
        if hasattr(self.listing, 'view_count'):
            self.listing.view_count = F('view_count') + 1
            self.listing.save(update_fields=['view_count'])

    def __str__(self):
        return f"{self.user} viewed {self.listing}"






