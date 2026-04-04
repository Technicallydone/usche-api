from rest_framework import serializers
from attendee.models import Attendee
from user.serializers import UserResponseSerializer 

class AttendeeSerializer(serializers.Serializer):
    attendee_id = serializers.UUIDField()
    participant = UserResponseSerializer()
    invitation_sent = serializers.BooleanField()
    status = serializers.CharField()