from rest_framework import serializers

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

