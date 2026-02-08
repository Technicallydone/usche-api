# user/serializers/user_profile.py
from rest_framework import serializers

from user.serializer.roles_response_serializer import RolesResponseSerializer

class UserProfileSerializer(serializers.Serializer):
    """
    Safe serializer for returning user profile with role and permissions.
    """
    user_id = serializers.UUIDField()
    first_name = serializers.CharField()
    middle_name = serializers.CharField(allow_null=True, required=False)
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    title = serializers.CharField()
    affiliation = serializers.CharField()
    occupation = serializers.CharField(allow_null=True, required=False)
    country = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    role = RolesResponseSerializer(allow_null=True)
