from rest_framework import permissions


class IsHost(permissions.BasePermission):
    """Разрешение только для пользователей с ролью хоста."""

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                hasattr(request.user, 'profile') and
                request.user.profile is not None and
                request.user.profile.roles.filter(name='host').exists()
        )

    def has_object_permission(self, request, view, obj):
        """Дополнительно: проверка, что хост - владелец объекта."""
        # Для бронирований:
        if hasattr(obj, 'listing') and hasattr(obj.listing, 'real_estate_object'):
            return obj.listing.real_estate_object.host == request.user

        # Для объектов недвижимости:
        if hasattr(obj, 'real_estate_object'):
            return obj.real_estate_object.host == request.user

        # Для других объектов с полем host:
        if hasattr(obj, 'host'):
            return obj.host == request.user

        return False


class IsGuest(permissions.BasePermission):
    """
    Разрешение только для пользователей с ролью гостя.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'profile') and \
            request.user.profile.roles.filter(name='guest').exists()


class IsHostOrReadOnly(permissions.BasePermission):
    """ Разрешение: хост может редактировать, остальные только читать."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Грузим нужные связи одним запросом
        if hasattr(obj, 'host'):
            return obj.host_id == request.user.id  # Сравниваем ID без загрузки объекта

        if hasattr(obj, 'real_estate_object'):
            # Используем select_related в queryset ViewSet
            return getattr(obj.real_estate_object, 'host_id', None) == request.user.id

        if hasattr(obj, 'listing'):
            return getattr(obj.listing.real_estate_object, 'host_id', None) == request.user.id

        return False


class IsReviewParticipant(permissions.BasePermission):
    """Разрешение для участников отзыва/рейтинга"""
    def has_object_permission(self, request, view, obj):
        # Для PropertyReview
        if hasattr(obj, 'guest'):
            return request.user in [obj.guest, obj.listing.real_estate_object.host]
        # Для UserRating
        elif hasattr(obj, 'rating_user'):
            return request.user in [obj.rating_user, obj.rated_user]
        return False