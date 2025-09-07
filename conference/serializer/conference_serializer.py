from rest_framework import serializers

from conference.models import Conference

class COnferenceSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Conference
        fields = '__all__'