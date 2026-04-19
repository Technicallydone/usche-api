from rest_framework import serializers

from themes.serializer.sub_theme_serializer import SubThemeSerializer

class ThemeSerializer(serializers.Serializer):
    theme_id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    sub_themes = SubThemeSerializer(many=True)