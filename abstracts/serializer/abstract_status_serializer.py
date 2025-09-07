from rest_framework import serializers


class AbstractStatusUpdateSerializer(serializers.Serializer):
    abstract_id = serializers.UUIDField()
    comment = serializers.CharField(required=False, allow_blank=True)