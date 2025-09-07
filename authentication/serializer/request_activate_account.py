from rest_framework import serializers

class RequestActivateAccount(serializers.Serializer):
    token = serializers.CharField(required=True)
