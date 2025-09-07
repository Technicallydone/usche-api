from attendee.models import Attendee
from rest_framework import serializers

from user.serializers import UserResponseSerializer


class AttendeeResponseSerializer(serializers.ModelSerializer):
    participant = UserResponseSerializer(many=False)
    
    class Meta:
        model = Attendee
        fields = '__all__'