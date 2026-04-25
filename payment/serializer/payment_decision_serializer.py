from rest_framework import serializers


class PaymentDecisionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=True)