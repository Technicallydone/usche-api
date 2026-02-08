from rest_framework import serializers

from user.serializer.permissions_response_serializer import PermissionsResponseSerializer

class RolesResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    permissions = PermissionsResponseSerializer(many=True)
