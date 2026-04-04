from rest_framework import serializers
from conference.models import BankAccount

class BankAccountSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    account_name = serializers.CharField()
    account_number = serializers.CharField()
    bank_name = serializers.CharField()
    currency = serializers.CharField()
    bank_code = serializers.CharField()
    swift_code = serializers.CharField()