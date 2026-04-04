from rest_framework import serializers

# --- Attendance stats ---
class AttendanceStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    attended_users = serializers.IntegerField()
    not_attended_users = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()


# --- Registrations per year ---
class RegistrationsPerYearSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    count = serializers.IntegerField()


# --- Recent registrations ---
class RecentRegistrationSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    created_at = serializers.DateTimeField()