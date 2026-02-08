from rest_framework import serializers

class CreateRoleRequestSerializer(serializers.Serializer):
    name = serializers.CharField(
        required=True,  # mandatory
        help_text="Role name (mandatory)"
    )