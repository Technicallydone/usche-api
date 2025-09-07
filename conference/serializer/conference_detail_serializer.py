from rest_framework import serializers

from attendee.serializer.attendee_serializer import AttendeeSerializer
from conference.models import Conference
from conference.serializer.bank_account_serializer import BankAccountSerializer
from conference.serializer.group_serializer import TargetGroupSerializer
from conference.serializer.resgistration_fee_serializer import RegistrationFeeSerializer
from conference.serializer.schedule_day_serializer import ScheduleDaySerializer
from speakers.serializer.speaker_serializer import SpeakerSerializer
from sponsors.serializer.sponsor_serializer import SponsorSerializer
from theme.serializer.themes_serializer import ThemeSerializer

class ConferenceDetailSerializer(serializers.ModelSerializer):
    sponsors = SponsorSerializer(many=True)
    speakers = SpeakerSerializer(many=True)
    attendees = AttendeeSerializer(many=True)
    theme = ThemeSerializer(many=True)
    registration_fees = RegistrationFeeSerializer(many=True)
    schedule_day = ScheduleDaySerializer(many=True, source='schedule_days')
    bank_accounts = BankAccountSerializer(many=True)
    groups = TargetGroupSerializer(many=True)

    class Meta:
        model = Conference
        fields = [
            'conference_id', 'conference_name', 'description', 'start_date',
            'end_date', 'start_time', 'end_time', 'venue_name', 'venue_website', 'venue_description', 'venue_directions',
            'capacity', 'listing_date', 'updated_at', 'abstract_submission_deadline', 'sponsors', 'speakers', 'attendees', 'theme',
            'registration_fees', 'schedule_day', 'bank_accounts', 'groups', 'registration_open'
        ]