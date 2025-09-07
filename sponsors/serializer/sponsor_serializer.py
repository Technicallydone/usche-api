from sponsors.models import Sponsor
from rest_framework import serializers

from usche_app import settings

class SponsorSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Sponsor
        fields = '__all__'
        
    def get_logo(self, obj):
        sponsor_id = obj.sponsor_id
        
        return f"{settings.SPONSOR_LOGO_BASE_URL}/{sponsor_id}/"