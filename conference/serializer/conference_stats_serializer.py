# src/conference/serializers.py
from rest_framework import serializers

class ConferenceStatsSerializer(serializers.Serializer):
    conference = serializers.DictField()
    attendees = serializers.DictField()
    abstracts = serializers.DictField()
    payments = serializers.DictField()