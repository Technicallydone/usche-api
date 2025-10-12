from rest_framework import serializers


class RequestJoinConferenceSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_slip = serializers.FileField(required=True)