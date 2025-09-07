from theme.models import SubTheme
from rest_framework import serializers

class SubThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTheme
        fields = '__all__'