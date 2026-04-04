from rest_framework import serializers
from conference.model.schedule_day import ScheduleDay
from conference.serializer.schedule_serializer import ConferenceScheduleSerializer

class ScheduleDaySerializer(serializers.Serializer):
    schedule_day_id = serializers.UUIDField()
    date = serializers.DateField()
    title = serializers.CharField()
    location = serializers.CharField()
    schedules = ConferenceScheduleSerializer(many=True, read_only=True)