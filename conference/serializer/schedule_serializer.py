from conference.models import ConferenceSchedule
from rest_framework import serializers

class ConferenceScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConferenceSchedule
        fields = '__all__'