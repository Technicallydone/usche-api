from rest_framework import serializers
from feedback.models import Option


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'option']