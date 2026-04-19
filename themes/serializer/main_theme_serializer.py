from themes.models import MainTheme
from rest_framework import serializers

class MainThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainTheme
        fields = '__all__'