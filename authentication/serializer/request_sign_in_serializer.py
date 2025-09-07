from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

class RequestSignInSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, data):
        user = authenticate(**data)

        if user is None:
            raise AuthenticationFailed(detail="Invalid credentials")

        if not user.is_active:
            raise PermissionDenied(detail="Your account is not activated")

        return user
