from rest_framework import serializers

from abstracts.model.abstract import Abstract
from payment.serializers import PaymentSerializer
from usche_app import settings
from user.serializers import UserResponseSerializer

class PaidAbstractSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(many=True, read_only=True)
    document = serializers.SerializerMethodField()
    user = UserResponseSerializer(many=False)

    class Meta:
        model = Abstract
        fields = '__all__'
        
    def get_document(self, obj):
        abstract_id = obj.abstract_id
        
        return f"{settings.ABSTRACT_DOCUMENT_URL}/{abstract_id}/"