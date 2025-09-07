import re
from rest_framework import serializers
from user.enums.title import TITLE_ENUM
from user.models import User

class RequestRegistration(serializers.Serializer):
    title = serializers.ChoiceField(choices=TITLE_ENUM.choices(), required=False)
    affiliation = serializers.CharField(max_length=255, required=False)
    first_name = serializers.CharField(max_length=150)
    middle_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=15, required=True)
    email = serializers.EmailField(required=True)
    country = serializers.CharField(max_length=100, required=False)
    occupation = serializers.CharField(max_length=100, required=True)
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(detail="This email is already registered. Try logging in instead.")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        pattern = re.compile(r'^\+?[1-9]\d{0,2}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}$')

        if not pattern.fullmatch(value):
            raise serializers.ValidationError("Invalid phone number format.")
        
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number already exists.")
        
        return value
    
    def validate_password(self, value):
        """Validate password strength (example: minimum length)"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        return value
