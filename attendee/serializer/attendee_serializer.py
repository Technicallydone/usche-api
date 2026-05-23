from rest_framework import serializers
from attendee.enums.attendee_status import AttendeeStatus
from attendee.models import Attendee
from conference.serializer.conference_serializer import ConferenceSerializer
from user.serializers import UserResponseSerializer 

class AttendeeSerializer(serializers.Serializer):
    attendee_id = serializers.UUIDField()
    participant = UserResponseSerializer()
    conference = ConferenceSerializer()
    invitation_sent = serializers.BooleanField()
    status = serializers.CharField()


class UpdateAttendeeStatusSerializer(serializers.Serializer):
    status = serializers.CharField()

    def validate_status(self, value: str):
        if not AttendeeStatus.validate(value):
            raise serializers.ValidationError(
                f"Invalid attendee status: {value}"
            )

        return value