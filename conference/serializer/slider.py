from rest_framework import serializers
from utils.image_validator import validate_image


class SliderBulkUploadSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    images = serializers.ListField(
        child=serializers.FileField(validators=[validate_image]),
        allow_empty=False
    )