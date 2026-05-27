from rest_framework import serializers

from utils.validator import validate_image_file

class CreateSponsorSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    name = serializers.CharField(max_length=255)
    website = serializers.URLField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    priority = serializers.IntegerField()
    
    logo = serializers.ImageField(
        required=True,
        validators=[validate_image_file]
    )
    
    def validate_priority(self, value):
        if value < 0:
            raise serializers.ValidationError("Priority must be a positive number.")
        return value

    def validate(self, data):
        if not data.get("website") and not data.get("contact_email"):
            raise serializers.ValidationError(
                "At least one of website or contact_email must be provided."
            )
        return data


class UpdateSponsorSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    website = serializers.URLField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    priority = serializers.IntegerField(required=False)
    logo = serializers.ImageField(
        required=False,
        validators=[validate_image_file]
    )

    def validate_priority(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Priority must be a positive number.")
        return value

    def validate(self, data):
        if "website" in data or "contact_email" in data:
            if not data.get("website") and not data.get("contact_email"):
                raise serializers.ValidationError(
                    "At least one of website or contact_email must be provided."
                )
        return data


class UpdateSponsorSerializer(serializers.Serializer):
    sponsor_id = serializers.UUIDField(required=True)

    name = serializers.CharField(max_length=255, required=False)
    website = serializers.URLField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    priority = serializers.IntegerField(required=False)

    logo = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_image_file]
    )