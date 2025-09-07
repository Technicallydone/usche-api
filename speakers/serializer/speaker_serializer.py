from rest_framework import serializers
from django.contrib.sites.shortcuts import get_current_site
from speakers.models import Speaker
from usche_app import settings

class SpeakerSerializer(serializers.ModelSerializer):
    # Override the passport field to return the full URL
    speaker_image = serializers.SerializerMethodField()

    class Meta:
        model = Speaker
        fields = '__all__'

    def get_speaker_image(self, obj):
        speaker_id = obj.speaker_id
        
        return f"{settings.SPEAKER_BASE_URL}/{speaker_id}/"
        