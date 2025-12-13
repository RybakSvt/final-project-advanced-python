from django.contrib import admin
from .models import User, Profile, Role


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    list_filter = ['is_staff', 'is_active']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
