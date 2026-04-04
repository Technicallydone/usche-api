from rest_framework import serializers
from sponsors.models import Sponsor
from usche_app import settings

class SponsorSerializer(serializers.Serializer):
    sponsor_id = serializers.UUIDField()
    name = serializers.CharField()
    logo = serializers.SerializerMethodField()
    website = serializers.URLField(allow_blank=True, required=False)
    contact_email = serializers.EmailField(allow_blank=True, required=False)
    priority = serializers.IntegerField()

    def get_logo(self, obj):
        return f"{settings.SPONSOR_LOGO_BASE_URL}/{obj.sponsor_id}/"