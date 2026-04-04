from rest_framework import serializers

from attendee.serializer.attendee_serializer import AttendeeSerializer
from conference.serializer.bank_account_serializer import BankAccountSerializer
from conference.serializer.group_serializer import TargetGroupSerializer
from conference.serializer.resgistration_fee_serializer import RegistrationFeeSerializer
from conference.serializer.schedule_day_serializer import ScheduleDaySerializer
from speakers.serializer.speaker_serializer import SpeakerSerializer
from sponsors.serializer.sponsor_serializer import SponsorSerializer
from theme.serializer.themes_serializer import ThemeSerializer
from usche_app import settings


class ConferenceDetailSerializer(serializers.Serializer):
    conference_id = serializers.CharField()
    conference_name = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)

    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    venue_name = serializers.CharField()
    venue_website = serializers.URLField(required=False, allow_blank=True)
    venue_description = serializers.CharField(required=False, allow_blank=True)
    venue_directions = serializers.CharField(required=False, allow_blank=True)

    capacity = serializers.IntegerField()
    listing_date = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    abstract_submission_deadline = serializers.DateTimeField()
    registration_open = serializers.BooleanField()
    
    certificate_background = serializers.SerializerMethodField()

    sponsors = SponsorSerializer(many=True)
    speakers = SpeakerSerializer(many=True)
    attendees = AttendeeSerializer(many=True)
    theme = ThemeSerializer(many=True)
    registration_fees = RegistrationFeeSerializer(many=True)

    schedule_days = ScheduleDaySerializer(many=True)
    bank_accounts = BankAccountSerializer(many=True)
    groups = TargetGroupSerializer(many=True)
    
    def get_certificate_background(self, obj):
        if not obj.certificate_background:
            return None
        return f"{settings.CERTIFICATE_BACKGROUND_BASE_URL}/{obj.conference_id}/certificate-template"