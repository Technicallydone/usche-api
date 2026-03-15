from rest_framework import serializers

class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)