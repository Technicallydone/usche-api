from rest_framework import serializers


class AbstractQuerySerializer(serializers.Serializer):
    conference_id= serializers.CharField(required=True)
    search = serializers.CharField(required=False, allow_blank=True)