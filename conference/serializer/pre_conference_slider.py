# src/conference/serializers/pre_conference_slider.py

from rest_framework import serializers


class PreConferenceSliderResponseSerializer(serializers.Serializer):
    image = serializers.SerializerMethodField()
