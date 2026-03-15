from rest_framework import serializers
from django.contrib.auth import authenticate

class RequestSignInSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)