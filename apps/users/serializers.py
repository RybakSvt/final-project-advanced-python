from rest_framework import serializers
from .models import User


class UserPublicSerializer(serializers.ModelSerializer):
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