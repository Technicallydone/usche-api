from rest_framework import serializers

class PermissionsResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code_name = serializers.CharField()
    description = serializers.CharField()