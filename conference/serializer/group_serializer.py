from conference.models import TargetGroup
from rest_framework import serializers

class TargetGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetGroup
        fields = '__all__'