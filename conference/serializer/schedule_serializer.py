from rest_framework import serializers
from conference.enum.session_type import SessionTypeEnum
from conference.models import ConferenceSchedule, ScheduleDay

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


class CreateConferenceScheduleSerializer(serializers.Serializer):
    schedule_day_id = serializers.UUIDField(required=True)

    date = serializers.DateField(required=True)

    start_time = serializers.TimeField(required=True)

    end_time = serializers.TimeField(required=True)

    activity = serializers.CharField(required=True)

    speaker = serializers.CharField(required=False, allow_blank=True)

    moderator = serializers.CharField(required=False, allow_blank=True)

    hall = serializers.CharField(required=False, allow_blank=True)

    session_type = serializers.ChoiceField(
        choices=SessionTypeEnum.choices()
    )

    def validate(self, data):
        schedule_day = ScheduleDay.objects.filter(
            schedule_day_id=data.get("schedule_day_id")
        ).first()

        if not schedule_day:
            raise serializers.ValidationError({
                "schedule_day_id": "Schedule day not found."
            })

        if data["date"] != schedule_day.date:
            raise serializers.ValidationError({
                "date": "Date must match schedule day date."
            })

        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError({
                "end_time": "End time must be after start time."
            })

        data["schedule_day"] = schedule_day
        return data


class UpdateConferenceScheduleSerializer(serializers.Serializer):
    schedule_id = serializers.UUIDField(required=True)

    date = serializers.DateField(required=False)

    start_time = serializers.TimeField(required=False)

    end_time = serializers.TimeField(required=False)

    activity = serializers.CharField(required=False)

    speaker = serializers.CharField(required=False, allow_blank=True)

    moderator = serializers.CharField(required=False, allow_blank=True)

    hall = serializers.CharField(required=False, allow_blank=True)

    session_type = serializers.ChoiceField(
        choices=SessionTypeEnum.choices(),
        required=False
    )

    def validate(self, data):
        schedule = ConferenceSchedule.objects.filter(
            schedule_id=data.get("schedule_id")
        ).first()

        if not schedule:
            raise serializers.ValidationError({
                "schedule_id": "Schedule not found."
            })

        date = data.get("date", schedule.date)
        start = data.get("start_time", schedule.start_time)
        end = data.get("end_time", schedule.end_time)

        if start >= end:
            raise serializers.ValidationError({
                "end_time": "End time must be after start time."
            })

        data["instance"] = schedule
        return data



