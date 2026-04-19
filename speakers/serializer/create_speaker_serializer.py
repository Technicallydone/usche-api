from rest_framework import serializers

from speakers.enum.speaker_enum import SPEAKER_CATEGORY, SPEAKER_TITLE
from utils.validator import validate_image_file

class CreateSpeakerSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)

    speaker_category = serializers.ChoiceField(
        choices=SPEAKER_CATEGORY.choices(),
        required=True
    )

    name = serializers.CharField(max_length=150, required=True)

    title = serializers.ChoiceField(
        choices=SPEAKER_TITLE.choices(),
        required=True
    )

    specialization = serializers.CharField(required=False, allow_blank=True)
    organization = serializers.CharField(required=True)
    role = serializers.CharField(required=False, allow_blank=True)

    biography = serializers.CharField(required=True)

    speaker_image = serializers.ImageField(
        required=True,
        validators=[validate_image_file]
    )


class UpdateSpeakerSerializer(serializers.Serializer):
    speaker_category = serializers.ChoiceField(
        choices=SPEAKER_CATEGORY.choices(),
        required=False
    )
    name = serializers.CharField(max_length=150, required=False)
    title = serializers.ChoiceField(
        choices=SPEAKER_TITLE.choices(),
        required=False,
        allow_null=True
    )
    specialization = serializers.CharField(required=False, allow_blank=True)
    organization = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(required=False, allow_blank=True)
    biography = serializers.CharField(required=False)
    speaker_image = serializers.ImageField(
        required=False,
        validators=[validate_image_file]
    )