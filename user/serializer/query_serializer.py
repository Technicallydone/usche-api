# user/serializers/query.py
from rest_framework import serializers

from attendee.enums.attendee_status import AttendeeStatus

class UserFilterQuerySerializer(serializers.Serializer):
    search_query = serializers.CharField(required=False, allow_blank=True)
    staff = serializers.BooleanField(required=False)
    created_from = serializers.DateField(required=False)
    created_to = serializers.DateField(required=False)
    conference_id = serializers.CharField(required=False)
    status = serializers.ChoiceField(
        choices=AttendeeStatus.choices(),
        required=False,
    )
    
    invitation_status = serializers.ChoiceField(
        choices=["sent", "not_sent"],
        required=False
    )