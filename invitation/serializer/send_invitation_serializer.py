
from rest_framework import serializers

class SendInvitationSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    users_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
