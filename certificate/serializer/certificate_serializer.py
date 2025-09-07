from rest_framework import serializers

class CertificateUserListSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
