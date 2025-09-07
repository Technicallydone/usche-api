from conference.models import BankAccount
from rest_framework import serializers

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'