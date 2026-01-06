from rest_framework import serializers
from apps.reviews.models import PropertyReview, UserRating
from apps.bookings.models import Booking
from apps.users.serializers import UserPublicSerializer

class ReviewPreviewSerializer(serializers.ModelSerializer):
    """Краткий отзыв для показа в карточке объявления"""
    guest_name = serializers.SerializerMethodField()
    guest_member_since = serializers.SerializerMethodField()

    class Meta:
        model = PropertyReview
        fields = ['id', 'rating', 'comment', 'created_at', 'guest_name', 'guest_member_since']

    def get_guest_name(self, obj):
        return f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username

    def get_guest_member_since(self, obj):
        return obj.guest.date_joined.year


class PropertyReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов на объявления"""
    guest_name = serializers.SerializerMethodField()
    guest_avatar = serializers.SerializerMethodField()

    class Meta:
        model = PropertyReview
        fields = [
            'id', 'booking', 'guest', 'listing', 'rating', 'comment',
            'is_approved', 'guest_name', 'guest_avatar', 'created_at'
        ]
        read_only_fields = ['guest', 'listing', 'is_approved', 'created_at']

    def get_guest_name(self, obj):
        return f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username

    def get_guest_avatar(self, obj):
        if hasattr(obj.guest, 'profile') and obj.guest.profile.avatar:
            return obj.guest.profile.avatar.url
        return None


    def validate(self, data):
        # Получаем booking_id из данных
        booking_id = data.get('booking')

        # Если это ID (при создании), получаем объект
        if isinstance(booking_id, int):
            try:
                booking = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                    raise serializers.ValidationError("Booking does not exist.")
        else:
                # Или используем существующий объект
                booking = booking_id or (self.instance.booking if self.instance else None)

        if not booking or booking.status != 'completed':
            raise serializers.ValidationError(
                "Review can only be created for completed bookings."
            )

        # Проверка: гость может оставить только один отзыв на бронирование
        if self.instance is None:  # только при создании
            if PropertyReview.objects.filter(booking=booking).exists():
                raise serializers.ValidationError(
                    "Review already exists for this booking."
                )

        # Проверка: отзыв может оставить только гость из бронирования
        request = self.context.get('request')
        if request and request.user != booking.guest:
            raise serializers.ValidationError(
                "Only the guest of this booking can leave a review."
            )

        return data


class UserRatingSerializer(serializers.ModelSerializer):
    """Сериализатор для рейтингов пользователей (все 3 оценки)"""
    rater_name = serializers.SerializerMethodField()
    rated_user_name = serializers.SerializerMethodField()
    scores = serializers.SerializerMethodField()

    class Meta:
        model = UserRating
        fields = [
            'id', 'booking', 'rating_user', 'rated_user',
            'satisfaction', 'friendliness', 'reliability',
            'comment', 'rater_name', 'rated_user_name', 'scores', 'created_at'
        ]
        read_only_fields = ['rating_user', 'rated_user', 'created_at']

    def get_rater_name(self, obj):
        return f"{obj.rating_user.first_name} {obj.rating_user.last_name}".strip() or obj.rating_user.username

    def get_rated_user_name(self, obj):
        return f"{obj.rated_user.first_name} {obj.rated_user.last_name}".strip() or obj.rated_user.username

    def get_scores(self, obj):
        return obj.scores


    def validate(self, data):

        booking_id = data.get('booking')

        # Если booking это ID
        if isinstance(booking_id, int):
            try:
                booking = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                raise serializers.ValidationError("Booking does not exist.")
        else:
            booking = booking_id or (self.instance.booking if self.instance else None)

        if not booking or booking.status != 'completed':
            raise serializers.ValidationError(
                "Rating can only be created for completed bookings."
            )

        # Сохраняется объект в data
        data['booking'] = booking
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        booking = validated_data['booking']

        # Автоматически определяется rated_user
        validated_data['rating_user'] = request.user
        if request.user == booking.guest:
            validated_data['rated_user'] = booking.listing.real_estate_object.host
        else:
            validated_data['rated_user'] = booking.guest

        return super().create(validated_data)


class PropertyReviewPublicSerializer(serializers.ModelSerializer):
    """Сериализатор для публичного показа отзывов (только одобренные)"""
    guest_name = serializers.SerializerMethodField()
    guest_member_since = serializers.SerializerMethodField()

    class Meta:
        model = PropertyReview
        fields = ['id', 'rating', 'comment', 'guest_name', 'guest_member_since', 'created_at']

    def get_guest_name(self, obj):
        return f"{obj.guest.first_name} {obj.guest.last_name}".strip() or obj.guest.username

    def get_guest_member_since(self, obj):
        return obj.guest.date_joined.year