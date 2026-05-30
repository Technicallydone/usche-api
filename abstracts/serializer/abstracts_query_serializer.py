from rest_framework import serializers

from abstracts.enums.abstract_status import AbstractStatus


class AbstractQuerySerializer(serializers.Serializer):
    conference_id= serializers.CharField(required=True)
    search = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=AbstractStatus.values(),
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class MyAbstractQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=AbstractStatus.values(),
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    def validate_status(self, value):
        if value in [None, ""]:
            return None

        return value.strip()