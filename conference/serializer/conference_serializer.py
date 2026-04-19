from rest_framework import serializers
from conference.models import Conference

class ConferenceSerailizer(serializers.Serializer):
    conference_id = serializers.UUIDField()
    conference_name = serializers.CharField()
    description = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    venue_name = serializers.CharField()
    venue_website = serializers.URLField(allow_blank=True, required=False)
    venue_description = serializers.CharField()
    venue_directions = serializers.CharField(allow_blank=True, required=False)
    capacity = serializers.IntegerField()
    abstract_submission_deadline = serializers.DateTimeField()
    certificate_background = serializers.FileField(allow_null=True, required=False)
    id_badge_background = serializers.FileField(allow_null=True, required=False)
    registration_open = serializers.BooleanField()
    year = serializers.CharField()
    listing_date = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()