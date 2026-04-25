from rest_framework import serializers

from abstracts.enums.abstract_status import AbstractStatus

class AbstractDecisionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=True)
