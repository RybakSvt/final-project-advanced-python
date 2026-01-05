from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.contrib.auth import get_user_model, authenticate
from .models import Profile, Role
from .serializers import (
    UserRegisterSerializer,
    UserProfileSerializer,
    EmailPasswordSerializer,
)


User = get_user_model()


class RegisterView(APIView):
    """Регистрация по email"""
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Создаем профиль если не создан
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)

        # Добавляем роль guest
        guest_role, _ = Role.objects.get_or_create(name='guest')
        user.profile.roles.add(guest_role)

        # Генерируем токены
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Вход по email и паролю"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Генерируем токены
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })


class LogoutView(APIView):
    """Выход"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()       # настройки blacklist в simplejwt

            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_205_RESET_CONTENT
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(APIView):
    """Профиль пользователя"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BecomeHostView(APIView):
    """Получить роль хоста"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)

        profile = user.profile
        host_role, _ = Role.objects.get_or_create(name='host')

        if profile.roles.filter(name='host').exists():
            return Response(
                {'message': 'User already has host role'},
                status=status.HTTP_200_OK
            )

        profile.roles.add(host_role)

        return Response({
            'message': 'Host role added successfully',
            'roles': list(profile.roles.values_list('name', flat=True))
        }, status=status.HTTP_200_OK)