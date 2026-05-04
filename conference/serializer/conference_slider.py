
from rest_framework import serializers
from conference.model.conference_slider import ConferenceSlider
from config.api_endpoints import APIEndpoints
from usche_app import settings


class ConferenceSliderResponseSerializer(serializers.Serializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj: ConferenceSlider):
        if not obj.image:
            return None
        return f"{APIEndpoints.CONFERENCE_SLIDERS}/{obj.id}/"