from rest_framework import permissions

class IsHost(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.roles.filter(name='host').exists()