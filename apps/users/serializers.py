from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate, get_user_model
from .models import User, Profile, Role


User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']


class ProfileSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            'phone', 'avatar', 'bio', 'roles',
            'satisfaction_total_score', 'satisfaction_votes_count',
            'friendliness_total_score', 'friendliness_votes_count',
            'reliability_total_score', 'reliability_votes_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'satisfaction_total_score', 'satisfaction_votes_count',
            'friendliness_total_score', 'friendliness_votes_count',
            'reliability_total_score', 'reliability_votes_count',
            'created_at', 'updated_at'
        ]


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "User with this email already exists."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class EmailPasswordSerializer(serializers.Serializer):
    """Сериализатор для входа по email и паролю"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError({
                'non_field_errors': 'Must provide email and password.'
            })

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError({
                'non_field_errors': 'Invalid email or password.'
            })

        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': 'User account is disabled.'
            })

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    profile = ProfileSerializer()
    roles = serializers.SerializerMethodField()
    member_since = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_joined', 'last_login', 'profile', 'roles', 'member_since'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def get_roles(self, obj):
        if hasattr(obj, 'profile'):
            return list(obj.profile.roles.values_list('name', flat=True))
        return []

    def get_member_since(self, obj):
        return obj.date_joined.strftime('%B %Y')

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data and hasattr(instance, 'profile'):
            profile = instance.profile
            for attr, value in profile_data.items():
                if attr not in ProfileSerializer.Meta.read_only_fields:
                    setattr(profile, attr, value)
            profile.save()

        return instance


class UserPublicSerializer(serializers.ModelSerializer):
    """Публичная информация о пользователе (для хоста о госте)"""
    member_since = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()

    def get_member_since(self, obj):
        return obj.date_joined.strftime('%B %Y')

    def get_ratings(self, obj):
        profile = getattr(obj, 'profile', None)
        if profile:
            return {
                'satisfaction': float(profile.satisfaction_total_score) if profile.satisfaction_total_score else 0.0,
                'friendliness': float(profile.friendliness_total_score) if profile.friendliness_total_score else 0.0,
                'reliability': float(profile.reliability_total_score) if profile.reliability_total_score else 0.0,
            }
        return {'satisfaction': 0.0, 'friendliness': 0.0, 'reliability': 0.0}

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name',
                  'member_since', 'ratings']