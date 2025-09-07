from rest_framework import serializers
from conference.model.schedule_day import ScheduleDay
from conference.serializer.schedule_serializer import ConferenceScheduleSerializer

class ScheduleDaySerializer(serializers.ModelSerializer):
    schedules = ConferenceScheduleSerializer(many=True, read_only=True) 

    class Meta:
        model = ScheduleDay
        fields = [
            'schedule_day_id',
            'date',
            'title',
            'location',
            'schedules',
        ]
