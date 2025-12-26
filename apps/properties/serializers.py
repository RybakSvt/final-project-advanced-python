from rest_framework import serializers
from .models import (
    RealEstateObject, RealEstateListing,
    Address, PropertyStats, Amenity
)


# ---------- Вспомогательные сериализаторы ----------
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

    # def validate(self, data):
    #     # Пропускаем проверку unique_together при обновлении
    #     return data


class PropertyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyStats
        fields = '__all__'


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'category']


# ---------- Основные сериализаторы RealEstateObject ----------
class RealEstateObjectListSerializer(serializers.ModelSerializer):
    """Короткий для списка"""
    full_address = serializers.CharField(source='address.full_address')

    class Meta:
        model = RealEstateObject
        fields = ['id', 'title', 'full_address', 'property_type', 'created_at']


class RealEstateObjectReadSerializer(serializers.ModelSerializer):
    address_raw = serializers.CharField()
    full_address = serializers.CharField(source='address.full_address')
    stats = PropertyStatsSerializer()
    amenities = AmenitySerializer(many=True)
    host_info = serializers.SerializerMethodField()

    class Meta:
        model = RealEstateObject
        fields = [
            'id', 'title', 'description', 'property_type',
            'address_raw', 'full_address', 'stats', 'amenities',
            'host_info', 'created_at', 'updated_at'
        ]

    def get_host_info(self, obj):
        """Информация о хосте """
        return {
            'id': obj.host.id,
            'username': obj.host.username,
            'name': f"{obj.host.first_name} {obj.host.last_name}".strip() or None
        }


class RealEstateObjectWriteSerializer(serializers.ModelSerializer):
    """Для создания и обновления (POST, PUT, PATCH)"""
    address_raw = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Original address entered by host (before normalization)'
    )
    address = AddressSerializer()
    stats = PropertyStatsSerializer()
    amenities = serializers.PrimaryKeyRelatedField(
        queryset=Amenity.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = RealEstateObject
        fields = [
            'title', 'description', 'property_type',
            'address_raw', 'address', 'stats', 'amenities'
        ]
        # host будет устанавливаться автоматически из request.user

    def create(self, validated_data):
        # Извлекаем данные
        address_raw = validated_data.pop('address_raw', '')
        address_data = validated_data.pop('address')
        stats_data = validated_data.pop('stats')
        amenities_data = validated_data.pop('amenities', [])

        # Находим или создаём нормализованный адрес
        address, _ = Address.objects.get_or_create(**address_data)

        # Создаём характеристики
        stats = PropertyStats.objects.create(**stats_data)

        # Создаём объект недвижимости
        obj = RealEstateObject.objects.create(
            address_raw=address_raw,
            address=address,
            stats=stats,
            **validated_data
        )

        # Привязываем удобства
        obj.amenities.set(amenities_data)
        return obj

    def update(self, instance, validated_data):
        # Обновляем обычные поля
        for attr, value in validated_data.items():
            if attr not in ['address_raw', 'address', 'stats', 'amenities']:
                setattr(instance, attr, value)

        # Обновляем сырой адрес
        if 'address_raw' in validated_data:
            instance.address_raw = validated_data.pop('address_raw')

        # Обновляем нормализованный адрес
        if 'address' in validated_data:
            address_data = validated_data.pop('address')
            address_data.pop('id', None)  # удаляем id, если передали

            # Ищем существующий адрес по новым данным
            try:
                new_address = Address.objects.get(
                    country=address_data.get('country'),
                    city=address_data.get('city'),
                    street=address_data.get('street'),
                    house_number=address_data.get('house_number'),
                    postal_code=address_data.get('postal_code')
                )
            except Address.DoesNotExist:
                # Создаём новый уникальный адрес
                new_address = Address.objects.create(**address_data)

            instance.address = new_address

        # Обновляем характеристики
        if 'stats' in validated_data:
            stats_data = validated_data.pop('stats')
            stats = instance.stats
            for key, value in stats_data.items():
                if key != 'id':
                    setattr(stats, key, value)
            stats.save()

        # Обновляем удобства
        if 'amenities' in validated_data:
            instance.amenities.set(validated_data.pop('amenities'))

        instance.save()
        return instance