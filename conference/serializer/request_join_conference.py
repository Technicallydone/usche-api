from rest_framework import serializers


class RequestJoinConferenceSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_slip = serializers.FileField(required=True)