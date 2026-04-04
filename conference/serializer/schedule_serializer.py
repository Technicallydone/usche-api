from rest_framework import serializers
from conference.models import ConferenceSchedule

class ConferenceScheduleSerializer(serializers.Serializer):
    schedule_id = serializers.UUIDField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    activity = serializers.CharField()
    speaker = serializers.CharField(allow_blank=True, required=False)
    moderator = serializers.CharField(allow_blank=True, required=False)
    hall = serializers.CharField(allow_blank=True, required=False)
    session_type = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()