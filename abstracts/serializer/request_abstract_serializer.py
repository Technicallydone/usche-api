import json

from rest_framework import serializers


class AbstractAuthorInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    affiliation = serializers.CharField(max_length=255)
    is_presenting_author = serializers.BooleanField(default=False)
    order = serializers.IntegerField(required=False, default=0)


class AbstractSubmissionSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)

    content = serializers.CharField(required=True)

    keywords = serializers.CharField(max_length=255, required=True)

    sub_theme = serializers.UUIDField(required=True)

    document = serializers.FileField(required=True)

    authors = serializers.JSONField(required=True)

    def validate_authors(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Authors must be a list."
            )

        if len(value) == 0:
            raise serializers.ValidationError(
                "At least one author is required."
            )

        serializer = AbstractAuthorInputSerializer(
            data=value,
            many=True,
        )

        serializer.is_valid(raise_exception=True)

        return serializer.validated_data

    def validate_keywords(self, value):
        keywords = [k.strip() for k in value.split(",")]

        if len(keywords) < 3 or len(keywords) > 5:
            raise serializers.ValidationError(
                "Keywords should contain between 3 and 5 keywords."
            )

        return value