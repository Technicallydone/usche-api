from rest_framework import serializers
from theme.models import MainTheme, SubTheme

class SubThemeSerializer(serializers.Serializer):
    sub_theme_id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()