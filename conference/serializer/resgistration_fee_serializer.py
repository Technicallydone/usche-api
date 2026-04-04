from rest_framework import serializers
from conference.models import RegistrationFee

class RegistrationFeeSerializer(serializers.Serializer):
    fee_id = serializers.UUIDField()
    conference_id = serializers.UUIDField(source="conference.conference_id")
    category = serializers.CharField()
    early_bird_fee = serializers.CharField()
    late_registration_fee = serializers.CharField()