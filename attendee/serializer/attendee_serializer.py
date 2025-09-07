from attendee.models import Attendee
from rest_framework import serializers


class AttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendee
        fields = '__all__'