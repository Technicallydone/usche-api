from rest_framework import serializers

class RequestChangePasswordSerailizer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(max_length=50, required=True)
