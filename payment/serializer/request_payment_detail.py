from rest_framework import serializers

class RequestPaymentDetailSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)