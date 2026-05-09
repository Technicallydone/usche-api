from rest_framework import serializers
from payment.models import Payment
from user.serializers import UserResponseSerializer


class PaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    user = UserResponseSerializer()

    abstract = serializers.PrimaryKeyRelatedField(read_only=True)
    conference = serializers.PrimaryKeyRelatedField(read_only=True)

    amount = serializers.CharField()

    payment_slip = serializers.SerializerMethodField()

    comment = serializers.CharField()
    status = serializers.CharField()

    rejected_by = serializers.PrimaryKeyRelatedField(read_only=True)

    timestamp = serializers.DateTimeField()

    def get_payment_slip(self, obj: Payment):
        return f"{self.context.get('payment_slip_url', '')}/{obj.payment_id}/"