import re
from rest_framework import serializers


class RequestJoinConferenceSerializer(serializers.Serializer):
    amount = serializers.CharField(required=True, max_length=50)
    payment_slip = serializers.FileField(required=True)

    def validate_amount(self, value):
        value = value.strip().upper()

        # Accept: 50 USD OR 50USD OR 50.5 TZS
        pattern = r"^(\d+(\.\d{1,2})?)\s?([A-Z]{3})$"

        match = re.match(pattern, value)
        if not match:
            raise serializers.ValidationError(
                "Amount must be in format like 50 USD or 100 TZS"
            )

        numeric_part = float(match.group(1))
        currency = match.group(3)

        if numeric_part <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")

        if numeric_part > 10_000_000:
            raise serializers.ValidationError("Amount exceeds allowed limit")

        # optional: attach parsed data if needed later
        return value

    def validate_payment_slip(self, file):
        if file.content_type != "application/pdf":
            raise serializers.ValidationError("Only PDF files are allowed")

        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File must be less than 5MB")

        return file