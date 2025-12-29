from rest_framework import permissions


class IsHost(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Проверяем наличие профиля
        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.roles.filter(name='host').exists()
