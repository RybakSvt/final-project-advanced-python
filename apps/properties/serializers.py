from rest_framework import serializers
from .models import (
    RealEstateObject, RealEstateListing,
    Address, PropertyStats, Amenity
)
from apps.reviews.serializers import ReviewPreviewSerializer


# ---------- Вспомогательные сериализаторы ----------
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


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


class ListingListSerializer(serializers.ModelSerializer):
    """Сериализатор списка объявлений (публичный и для хоста)"""
    # Поля из RealEstateObject
    title = serializers.CharField(source='real_estate_object.title')
    property_type = serializers.CharField(source='real_estate_object.property_type')
    rooms = serializers.IntegerField(source='real_estate_object.stats.rooms')
    city = serializers.CharField(source='real_estate_object.address.city')

    # Рейтинг и отзывы (будут позже)
    rating_avg = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    # Фото (заглушка)
    image_urls = serializers.SerializerMethodField()

    # Поля для хоста (скрыты в публичном API)
    is_active = serializers.BooleanField()
    is_approved = serializers.BooleanField()
    view_count = serializers.IntegerField()

    class Meta:
        model = RealEstateListing
        fields = [
            'id',
            'title',
            'promo_title',
            'property_type',
            'rooms',
            'city',
            'rating_avg',
            'reviews_count',
            'price_per_night',
            'currency',
            'image_urls',
            'is_active',  # видит только хост
            'is_approved',  # видит только хост
            'view_count',  # видит только хост
            'created_at'
        ]

    def get_rating_avg(self, obj):
        # TODO: рассчитать средний рейтинг из PropertyReview
        return 4.5  # заглушка

    def get_reviews_count(self, obj):
        # TODO: количество отзывов
        return 12  # заглушка

    def get_image_urls(self, obj):
        # TODO: когда будут фото — вернуть список URL
        return []  # заглушка

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        # Проверяем, является ли пользователь хостом этого объявления
        is_host = (
                request and
                request.user.is_authenticated and
                request.user == instance.real_estate_object.host
        )

        if not is_host:
            # Скрываем поля хоста для не-владельцев
            data.pop('is_active', None)
            data.pop('is_approved', None)
            data.pop('view_count', None)

        return data


class ListingReadSerializer(serializers.ModelSerializer):
    """Детальный просмотр объявления (публичный для всех)"""

    # Основные данные из объекта недвижимости
    title = serializers.CharField(source='real_estate_object.title')
    description = serializers.CharField(source='real_estate_object.description')
    property_type = serializers.CharField(source='real_estate_object.property_type')

    # Адрес (только город)
    city = serializers.CharField(source='real_estate_object.address.city')

    # Характеристики
    rooms = serializers.IntegerField(source='real_estate_object.stats.rooms')
    bathrooms = serializers.IntegerField(source='real_estate_object.stats.bathrooms')
    area_sqm = serializers.IntegerField(source='real_estate_object.stats.area_sqm')
    max_guests = serializers.IntegerField(source='real_estate_object.stats.max_guests')

    # Удобства
    amenities = AmenitySerializer(
        source='real_estate_object.amenities',
        many=True
    )

    # Рейтинг и отзывы
    rating_avg = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()

    # Фото (заглушка)
    images = serializers.SerializerMethodField()

    # Правила
    rules = serializers.SerializerMethodField()

    # Информация о хосте (публичная)
    host = serializers.SerializerMethodField()

    class Meta:
        model = RealEstateListing
        fields = [
            'id',
            'title',
            'promo_title',
            'description',
            'property_type',
            'city',
            'rooms',
            'bathrooms',
            'area_sqm',
            'max_guests',
            'amenities',
            'price_per_night',
            'currency',
            'rating_avg',
            'reviews_count',
            'recent_reviews',
            'images',
            'rules',
            'host',
            'created_at'
        ]

    def get_rating_avg(self, obj):
        # TODO: средний рейтинг из PropertyReview
        return 4.5

    def get_reviews_count(self, obj):
        # TODO: количество отзывов
        return 12

    def get_recent_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True).order_by('-created_at')[:4]
        return ReviewPreviewSerializer(reviews, many=True, context=self.context).data

    def get_images(self, obj):
        # TODO: список URL фото
        return []

    def get_rules(self, obj):
        return {
            'minimum_stay': obj.minimum_stay,
            'check_in_time': obj.check_in_time,
            'check_out_time': obj.check_out_time,
            'cancellation_days_before': obj.cancellation_days_before
        }

    def get_host(self, obj):
        host = obj.real_estate_object.host
        profile = host.profile if hasattr(host, 'profile') else None

        return {
            'id': host.id,
            'username': host.username,
            'member_since': host.date_joined.strftime('%B %Y'),
            'ratings': {
                'satisfaction': profile.satisfaction_total_score if profile else 0,
                'friendliness': profile.friendliness_total_score if profile else 0,
                'reliability': profile.reliability_total_score if profile else 0,
            } if profile else None
        }


class ListingHostDetailSerializer(ListingReadSerializer):
    """Детальный просмотр объявления для хоста (со служебными полями и фото)"""

    # Служебные поля
    is_active = serializers.BooleanField()
    is_approved = serializers.BooleanField()
    view_count = serializers.IntegerField()
    moderation_notes = serializers.CharField(read_only=True)

    # Фото - после создания модели ListingImage:
    images = serializers.SerializerMethodField()

    class Meta(ListingReadSerializer.Meta):
        fields = ListingReadSerializer.Meta.fields + [
            'is_active',
            'is_approved',
            'view_count',
            'moderation_notes',
            'images'
        ]

    def get_images(self, obj):
        """Возвращает список фото объявления"""
        # После создания модели ListingImage:
        # return [img.image.url for img in obj.images.all()]
        return []  # заглушка


class ListingWriteSerializer(serializers.ModelSerializer):
    """Создание и обновление объявлений (для хоста)"""

    # Поле для загрузки фото (массив файлов, опционально)
    upload_images = serializers.ListField(
        child=serializers.ImageField(max_length=100, allow_empty_file=False),
        write_only=True,
        required=False,
        help_text='Список загружаемых фотографий'
    )

    real_estate_object = serializers.PrimaryKeyRelatedField(
        queryset=RealEstateObject.objects.all(),
        write_only=True
    )

    class Meta:
        model = RealEstateListing
        fields = [
            'real_estate_object',
            'price_per_night',
            'currency',
            'minimum_stay',
            'check_in_time',
            'check_out_time',
            'cancellation_days_before',
            'is_active',
            'promo_title',
            'upload_images'  # только для записи
        ]
        read_only_fields = ['real_estate_object']

    def validate(self, data):
        user = self.context['request'].user
        real_estate_object = data.get('real_estate_object')

        if real_estate_object and real_estate_object.host != user:
            raise serializers.ValidationError({
                'real_estate_object': 'You can only create listings for your own properties.'
            })
        return data

    def create(self, validated_data):
        upload_images = validated_data.pop('upload_images', [])
        listing = super().create(validated_data)

        # После создания модели ListingImage
        # for img in upload_images:
        #     ListingImage.objects.create(listing=listing, image=img)

        return listing

    def update(self, instance, validated_data):
        upload_images = validated_data.pop('upload_images', [])
        validated_data.pop('real_estate_object', None)
        listing = super().update(instance, validated_data)

        # Добавление новых фото
        # for img in upload_images:
        #     ListingImage.objects.create(listing=listing, image=img)

        return listing