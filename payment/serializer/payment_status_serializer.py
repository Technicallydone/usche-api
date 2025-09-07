from rest_framework import serializers


class PaymentStatusUpdateSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    comment = serializers.CharField(required=False, allow_blank=True)