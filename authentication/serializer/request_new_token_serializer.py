from rest_framework import serializers

class RequestNewToken(serializers.Serializer):
    token = serializers.CharField(required=True)
