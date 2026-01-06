from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Count, Case, When, IntegerField
from .models import UserRating
from apps.users.models import Profile


@receiver([post_save, post_delete], sender=UserRating)
def update_profile_ratings(sender, instance, **kwargs):
    """Обновляет агрегированные рейтинги в профиле."""
    # Используется on_commit чтобы избежать проблем с транзакциями
    transaction.on_commit(lambda: _update_profile_stats(instance.rated_user_id))


def _update_profile_stats(user_id):
    """Пересчитывает статистику рейтингов для пользователя по его ID."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    if not hasattr(user, 'profile'):
        return

    profile = user.profile

    # Агрегирует данные одним запросом для каждой категории
    categories = ['satisfaction', 'friendliness', 'reliability']

    for category in categories:
        # статистику по категории одним запросом
        stats = UserRating.objects.filter(
            rated_user_id=user_id
        ).aggregate(
            total_top=Count(Case(
                When(**{f'{category}': 'TOP'}, then=1),
                output_field=IntegerField()
            )),
            total_ok=Count(Case(
                When(**{f'{category}': 'OK'}, then=1),
                output_field=IntegerField()
            )),
            total_poor=Count(Case(
                When(**{f'{category}': 'POOR'}, then=1),
                output_field=IntegerField()
            )),
            total_count=Count(f'{category}')
        )

        # Вычисление суммарного балла
        total_score = (
                stats['total_top'] * 100 +
                stats['total_ok'] * 50 +
                stats['total_poor'] * 0
        )

        # Сохранение в профиль
        setattr(profile, f'{category}_total_score', total_score)
        setattr(profile, f'{category}_votes_count', stats['total_count'])
        setattr(profile, f'{category}_top_count', stats['total_top'])
        setattr(profile, f'{category}_ok_count', stats['total_ok'])
        setattr(profile, f'{category}_poor_count', stats['total_poor'])

    # Сохранение всех изменений одним запросом
    update_fields = []
    for category in categories:
        update_fields.extend([
            f'{category}_total_score',
            f'{category}_votes_count',
            f'{category}_top_count',
            f'{category}_ok_count',
            f'{category}_poor_count'
        ])
    update_fields.append('updated_at')

    profile.save(update_fields=update_fields)


@receiver(post_save, sender=UserRating)
def update_rating_user_stats(sender, instance, created, **kwargs):
    """Также обновновление статистику для пользователя, который поставил оценку."""
    if created:
        transaction.on_commit(
            lambda: _update_rating_user_stats(instance.rating_user_id)
        )


def _update_rating_user_stats(user_id):
    """Обновление статистику пользователя как оценщика."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    if not hasattr(user, 'profile'):
        return

    # Обновление счетчика поставленных оценок
    from .models import UserRating
    ratings_given = UserRating.objects.filter(rating_user_id=user_id).count()
    user.profile.ratings_given_count = ratings_given
    user.profile.save(update_fields=['ratings_given_count', 'updated_at'])