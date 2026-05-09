from rest_framework import serializers


class UploadPaymentSlipSerializer(serializers.Serializer):
    abstract_id = serializers.UUIDField(required=True)
    amount = serializers.CharField()
    payment_slip = serializers.FileField(required=True)
