from rest_framework import serializers


class ConferenceStatsSerializer(serializers.Serializer):
    overview = serializers.DictField()
    abstracts = serializers.DictField()
    payments = serializers.DictField()
    themes = serializers.DictField()
    trends = serializers.DictField()
    top_conferences = serializers.ListField()