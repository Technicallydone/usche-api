from rest_framework import serializers

from user.model.user import User

class UserResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model to include relevant user details.
    """
    class Meta:
        model = User
        fields = ['title', 'user_id', 'first_name', 'middle_name', 'last_name', 'email', 'phone_number', 'country', 'occupation', 'affiliation', 'is_active']