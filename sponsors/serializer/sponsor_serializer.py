from rest_framework import serializers
from config.api_endpoints import APIEndpoints
from sponsors.models import Sponsor
from usche_app import settings

class SponsorSerializer(serializers.Serializer):
    sponsor_id = serializers.UUIDField()
    name = serializers.CharField()
    logo = serializers.SerializerMethodField()
    website = serializers.URLField(allow_blank=True, required=False)
    contact_email = serializers.EmailField(allow_blank=True, required=False)
    priority = serializers.IntegerField()

    def get_logo(self, obj: Sponsor):
        return f"{APIEndpoints.SPONSOR_LOGO}/{obj.sponsor_id}/"