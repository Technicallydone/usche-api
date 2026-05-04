# src/conference/serializers/pre_conference_slider.py

from rest_framework import serializers
from conference.model.pre_conference_slider import PreConferenceSlider
from config.api_endpoints import APIEndpoints
from usche_app import settings


class PreConferenceSliderResponseSerializer(serializers.Serializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj: PreConferenceSlider):
        if not obj.image:
            return None
        return f"{APIEndpoints.PRE_CONFERENCE_SLIDERS}/{obj.id}/"