from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from user.models import User
from user.enums.title import TITLE_ENUM


class RequestRegistration(serializers.Serializer):
    title = serializers.ChoiceField(choices=TITLE_ENUM.choices(), required=True)
    affiliation = serializers.CharField(max_length=255, required=True)
    first_name = serializers.CharField(max_length=30, required=True)
    middle_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=True)
    phone_number = serializers.CharField(max_length=15, required=True)
    email = serializers.EmailField(required=True)
    country = serializers.CharField(max_length=100, required=True)
    occupation = serializers.CharField(max_length=100, required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate_first_name(self, value):
        return value.strip().capitalize()[:30]

    def validate_middle_name(self, value):
        return value.strip().capitalize()[:30] if value else value

    def validate_last_name(self, value):
        return value.strip().capitalize()[:30]

    def validate_country(self, value):
        return value.strip().capitalize()[:100]

    def validate_password(self, value):
        import re

        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError("Must contain uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError("Must contain lowercase letter.")
        if not re.search(r"\d", value):
            raise serializers.ValidationError("Must contain number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\\[\]]", value):
            raise serializers.ValidationError("Must contain special character.")

        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

        return value

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()

        if user:
            if user.is_active:
                raise serializers.ValidationError(
                    "This email is already registered and active. Please login or use a different email."
                )

            # pass existing inactive user to view
            self.context["existing_user"] = user

        return value