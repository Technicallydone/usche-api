from rest_framework import serializers

class RequestRetrieveSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)