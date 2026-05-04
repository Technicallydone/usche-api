from rest_framework import serializers

from config.api_endpoints import APIEndpoints
from payment.models import Payment
from usche_app import settings
from user.serializers import UserResponseSerializer

class CompletedPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model, including user details.
    """
    user = UserResponseSerializer() 

    payment_slip = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = '__all__'
        
    def get_payment_slip(self, obj: Payment):
        payment_id = obj.payment_id
        
        return f"{APIEndpoints.PAYMENT_SLIP}/{payment_id}/"