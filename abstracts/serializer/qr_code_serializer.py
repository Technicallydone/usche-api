from rest_framework import serializers

class QRCodeVerificationSerializer(serializers.Serializer):
    qr_data = serializers.CharField(required=True, help_text="QR Code data containing USER_ID and EMAIL")
