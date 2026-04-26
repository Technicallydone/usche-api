# src/conference/serializers/conference_slider.py

from rest_framework import serializers

class ConferenceSliderResponseSerializer(serializers.Serializer):
    image = serializers.SerializerMethodField()
