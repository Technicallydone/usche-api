from rest_framework import serializers
from conference.models import TargetGroup

class TargetGroupSerializer(serializers.Serializer):
    group_id = serializers.UUIDField()
    group_name = serializers.CharField()