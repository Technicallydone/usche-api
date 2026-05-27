from rest_framework import serializers
from conference.models import Conference, ScheduleDay
from conference.serializer.schedule_serializer import ConferenceScheduleSerializer

class ScheduleDaySerializer(serializers.Serializer):
    schedule_day_id = serializers.UUIDField()
    date = serializers.DateField()
    title = serializers.CharField()
    location = serializers.CharField()
    schedules = ConferenceScheduleSerializer(many=True, read_only=True)


class CreateScheduleDaySerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)

    date = serializers.DateField(required=True)

    title = serializers.CharField(
        required=True,
        max_length=255
    )

    location = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255
    )

    def validate(self, data):
        conference = Conference.objects.filter(
            conference_id=data.get("conference_id")
        ).first()

        if not conference:
            raise serializers.ValidationError({
                "conference_id": "Conference not found."
            })

        data["conference"] = conference
        return data


class UpdateScheduleDaySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    title = serializers.CharField(max_length=255, required=False)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)


class UpdateScheduleDaySerializer(serializers.Serializer):
    schedule_day_id = serializers.UUIDField(required=True)

    date = serializers.DateField(required=False)

    title = serializers.CharField(required=False, max_length=255)

    location = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate(self, data):
        schedule_day = ScheduleDay.objects.filter(
            schedule_day_id=data.get("schedule_day_id")
        ).first()

        if not schedule_day:
            raise serializers.ValidationError({
                "schedule_day_id": "Schedule day not found."
            })

        data["instance"] = schedule_day
        return data