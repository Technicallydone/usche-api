from theme.models import MainTheme
from rest_framework import serializers

from theme.serializer.sub_theme_serializer import SubThemeSerializer

class ThemeSerializer(serializers.ModelSerializer):
    sub_themes = SubThemeSerializer(many=True)

    class Meta:
        model = MainTheme
        fields = '__all__'