from conference.models import RegistrationFee
from rest_framework import serializers

class RegistrationFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationFee
        fields = '__all__'