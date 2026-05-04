from rest_framework import serializers
from config.api_endpoints import APIEndpoints
from payment.models import Payment
from usche_app import settings
from user.serializers import UserResponseSerializer

class ConferencePaymentReportSerializer(serializers.ModelSerializer):
    user = UserResponseSerializer()
    abstract = serializers.SerializerMethodField()
    payment_slip = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = '__all__'

    def get_payment_slip(self, obj: Payment):
        return f"{APIEndpoints.PAYMENT_SLIP}/{obj.payment_id}/"

    def get_abstract(self, obj):
        from abstracts.serializers import AbstractSerializer
        if obj.abstract:
            return AbstractSerializer(obj.abstract).data
        return None
