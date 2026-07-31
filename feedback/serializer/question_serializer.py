from feedback.models import Question
from rest_framework import serializers

from feedback.enums.question_type import QuestionTypeEnum


class CreateQuestionOptionSerializer(serializers.Serializer):
    option = serializers.CharField(max_length=255, required=True)
    position = serializers.IntegerField(required=True, min_value=1)


class CreateQuestionSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)

    question = serializers.CharField(required=True)

    type = serializers.ChoiceField(
        choices=QuestionTypeEnum.choices(),
        required=True,
    )

    is_required = serializers.BooleanField(default=True)

    position = serializers.IntegerField(
        required=True,
        min_value=1,
    )

    options = CreateQuestionOptionSerializer(
        many=True,
        required=False,
        default=[],
    )


class UpdateQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(required=False)

    type = serializers.ChoiceField(
        choices=QuestionTypeEnum.choices(),
        required=False,
    )

    is_required = serializers.BooleanField(required=False)

    position = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    options = CreateQuestionOptionSerializer(
        many=True,
        required=False,
    )


class CreateQuestionOptionOnlySerializer(serializers.Serializer):
    question_id = serializers.UUIDField(required=True)

    option = serializers.CharField(
        max_length=255,
        required=True,
    )

    position = serializers.IntegerField(
        required=True,
        min_value=1,
    )


class UpdateQuestionOptionSerializer(serializers.Serializer):
    option = serializers.CharField(
        max_length=255,
        required=False,
    )

    position = serializers.IntegerField(
        required=False,
        min_value=1,
    )


class QuestionFilterQuerySerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)

class QuestionOptionSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    option = serializers.CharField(read_only=True)
    position = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class QuestionSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    conference_id = serializers.UUIDField(read_only=True)

    question = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)

    is_required = serializers.BooleanField(read_only=True)
    position = serializers.IntegerField(read_only=True)

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    options = QuestionOptionSerializer(
        many=True,
        read_only=True,
    )

    def to_representation(self, instance: Question):
        return {
            "id": instance.id,
            "conference_id": instance.conference.conference_id,
            "question": instance.question,
            "type": instance.type,
            "is_required": instance.is_required,
            "position": instance.position,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
            "options": QuestionOptionSerializer(
                instance.options.all(),
                many=True,
            ).data,
        }