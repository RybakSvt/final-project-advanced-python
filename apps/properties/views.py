from rest_framework import viewsets, permissions
from .models import RealEstateObject
from .serializers import (
    RealEstateObjectListSerializer,
    RealEstateObjectReadSerializer,
    RealEstateObjectWriteSerializer
)
from ..shared.permissions import IsHost


class RealEstateObjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для объектов недвижимости.
    Хост видит только свои объекты.
    """
#    permission_classes = [permissions.IsAuthenticated, IsHost]
    #http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        return RealEstateObject.objects.filter(host=self.request.user)

    # def get_serializer_class(self):
    #     if self.action in ['list', 'retrieve']:
    #         return RealEstateObjectReadSerializer
    #     return RealEstateObjectWriteSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return RealEstateObjectListSerializer
        if self.action == 'retrieve':
            return RealEstateObjectReadSerializer
        return RealEstateObjectWriteSerializer

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)