from rest_framework import serializers

from payment.models import Payment
from usche_app import settings
from user.serializers import UserResponseSerializer

class PaymentSerializer(serializers.ModelSerializer):
    payment_slip = serializers.SerializerMethodField()
    user = UserResponseSerializer() 
    
    class Meta:
        model = Payment
        fields = '__all__'
        
    def get_payment_slip(self, obj):
        payment_id = obj.payment_id
        
        return f"{settings.PAYMENT_SLIP_URL}/{payment_id}/"