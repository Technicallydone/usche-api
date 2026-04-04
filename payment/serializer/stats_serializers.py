from rest_framework import serializers

class PaymentActivityStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    active_percentage = serializers.FloatField()
