from rest_framework import serializers
from config.api_endpoints import APIEndpoints
from speakers.models import Speaker
from usche_app import settings

class SpeakerSerializer(serializers.Serializer):
    speaker_id = serializers.UUIDField()
    speaker_category = serializers.CharField()
    name = serializers.CharField()
    title = serializers.CharField(allow_blank=True, required=False)
    specialization = serializers.CharField(allow_blank=True, required=False)
    organization = serializers.CharField(allow_blank=True, required=False)
    role = serializers.CharField(allow_blank=True, required=False)
    biography = serializers.CharField()
    speaker_image = serializers.SerializerMethodField()

    def get_speaker_image(self, obj: Speaker):
        return f"{APIEndpoints.SPEAKER_IMAGE}/{obj.speaker_id}/"