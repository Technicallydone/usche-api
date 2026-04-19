from rest_framework import serializers

from conference.enum.session_type import SessionTypeEnum
from conference.model.schedule_day import ScheduleDay
from utils.validator import validate_svg

class SVGUploadSerializer(serializers.Serializer):
    file = serializers.FileField(
        required=True,
        validators=[validate_svg]
    )

class CreateConferenceSerializer(serializers.Serializer):
    conference_name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=True)
    end_time = serializers.TimeField(required=True)
    capacity = serializers.IntegerField(required=True)
    abstract_submission_deadline = serializers.DateTimeField(required=True)
    registration_open = serializers.BooleanField()
    year = serializers.CharField(required=True)
    certificate_background = serializers.FileField(
        required=True,
        validators=[validate_svg]
    )

    id_badge_background = serializers.FileField(
        required=True,
        validators=[validate_svg]
    )


class CreateVenueSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    venue_name = serializers.CharField(max_length=255, required=True)
    venue_website = serializers.URLField(required=False)
    venue_description = serializers.CharField(required=True)
    venue_directions = serializers.CharField(required=False)


class CreateRegistrationFeeSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    category = serializers.CharField(max_length=255, required=True)
    early_bird_fee = serializers.CharField(max_length=100, required=True)
    late_registration_fee = serializers.CharField(max_length=100, required=True)


class CreateTargetGroupSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    group_name = serializers.CharField(max_length=255, required=True)


class CreateBankAccountSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    account_name = serializers.CharField(max_length=255, required=True)
    account_number = serializers.CharField(max_length=50, required=True)
    bank_name = serializers.CharField(max_length=255, required=True)
    currency = serializers.CharField(max_length=50, required=True)
    bank_code = serializers.CharField(max_length=10, required=True)
    swift_code = serializers.CharField(max_length=20, required=True)


class CreateScheduleDaySerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    date = serializers.DateField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)


class CreateConferenceScheduleSerializer(serializers.Serializer):
    schedule_day_id = serializers.UUIDField(required=True)
    date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=True)
    end_time = serializers.TimeField(required=True)
    activity = serializers.CharField(required=False, allow_blank=True, default="")
    speaker = serializers.CharField(required=False, allow_blank=True)
    moderator = serializers.CharField(required=False, allow_blank=True)
    hall = serializers.CharField(required=False, allow_blank=True)
    session_type = serializers.ChoiceField(
        choices=SessionTypeEnum.choices(),
        required=False,
        default=SessionTypeEnum.default()
    )

    def validate(self, data):
        # Validate start_time < end_time
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        # Validate date matches schedule_day date
        schedule_day_id = data.get("schedule_day_id")
        if schedule_day_id:
            try:
                schedule_day = ScheduleDay.objects.get(schedule_day_id=schedule_day_id)
                if data.get("date") != schedule_day.date:
                    raise serializers.ValidationError(
                        "Schedule date must match the associated schedule day date."
                    )
            except ScheduleDay.DoesNotExist:
                raise serializers.ValidationError("Associated ScheduleDay not found.")
        return data


# UPDATE PART


class UpdateConferenceSerializer(serializers.Serializer):
    conference_name = serializers.CharField(max_length=255)
    description = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    capacity = serializers.IntegerField()
    abstract_submission_deadline = serializers.DateTimeField()
    registration_open = serializers.BooleanField()
    year = serializers.CharField()


class UpdateRegistrationFeeSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=255, required=False)
    early_bird_fee = serializers.CharField(max_length=100, required=False)
    late_registration_fee = serializers.CharField(max_length=100, required=False)


class UpdateTargetGroupSerializer(serializers.Serializer):
    group_name = serializers.CharField(max_length=255, required=False)


class UpdateBankAccountSerializer(serializers.Serializer):
    account_name = serializers.CharField(max_length=255, required=False)
    account_number = serializers.CharField(max_length=50, required=False)
    bank_name = serializers.CharField(max_length=255, required=False)
    currency = serializers.CharField(max_length=50, required=False)
    bank_code = serializers.CharField(max_length=10, required=False)
    swift_code = serializers.CharField(max_length=20, required=False)


class UpdateConferenceScheduleSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    activity = serializers.CharField(required=False, allow_blank=True)
    speaker = serializers.CharField(required=False, allow_blank=True)
    moderator = serializers.CharField(required=False, allow_blank=True)
    hall = serializers.CharField(required=False, allow_blank=True)
    session_type = serializers.ChoiceField(
        choices=SessionTypeEnum.choices(),
        required=False
    )

    def validate(self, data):
        # Validate start_time < end_time if both are provided
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        # If date is updated, ensure it matches schedule_day
        if "date" in data:
            if not hasattr(self.instance, "schedule_day"):
                raise serializers.ValidationError("Cannot validate date without schedule_day.")
            if data["date"] != self.instance.schedule_day.date:
                raise serializers.ValidationError(
                    "Updated schedule date must match the associated schedule day date."
                )

        return data


class UpdateScheduleDaySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    title = serializers.CharField(max_length=255, required=False)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
