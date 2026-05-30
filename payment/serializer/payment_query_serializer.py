from rest_framework import serializers
from payment.enums.payment_status import PaymentStatus

class PaymentQuerySerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)

    status = serializers.ChoiceField(
        choices=PaymentStatus.values(),
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    search = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=255,
    )

    def validate_status(self, value):
        if value in [None, ""]:
            return None
        return value.strip()

    def validate_search(self, value: str):
        if value in [None, ""]:
            return None
        return value.strip().lower()


class MyPaymentQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=PaymentStatus.values(),
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    def validate_status(self, value):
        if value in [None, ""]:
            return None

        return value.strip()