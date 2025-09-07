from rest_framework import serializers

from attendee.models import Attendee
from user.serializers import UserResponseSerializer

class UninvitedAttendeeSerializer(serializers.ModelSerializer):
    """Serializer for attendees who haven't received invitations, including user details"""
    
    participant = UserResponseSerializer()

    class Meta:
        model = Attendee
        fields = ["attendee_id", "conference", "participant", "status", "invitation_sent"]