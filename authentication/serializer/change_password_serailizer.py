import re
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

class RequestChangePasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, max_length=50)

    def validate_new_password(self, value):
        """
        Strong password validation:
        - Minimum 8 characters
        - At least one uppercase
        - At least one lowercase
        - At least one digit
        - At least one special character
        - Not too common
        """
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )

        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r'\d', value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=/\\\[\]]', value):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )

        # Optional: Django’s built-in validators (checks for common passwords, similarity, etc.)
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

        return value