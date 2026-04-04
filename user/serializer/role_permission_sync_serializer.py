from rest_framework import serializers

class RolePermissionSyncSerializer(serializers.Serializer):
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        allow_empty=True,
        help_text="List of permission UUIDs to sync with the role"
    )
