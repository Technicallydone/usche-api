from rest_framework import serializers
from certificate.models import Certificate
from user.serializers import UserResponseSerializer


class CertificateResponseSerializer(serializers.ModelSerializer):
    user = UserResponseSerializer()

    class Meta:
        model = Certificate
        fields = ["certificate_id", "user", "issued_at", "is_sent"]
