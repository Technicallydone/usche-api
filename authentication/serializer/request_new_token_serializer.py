from rest_framework import serializers

class RequestNewToken(serializers.Serializer):
    email = serializers.CharField(required=True)
