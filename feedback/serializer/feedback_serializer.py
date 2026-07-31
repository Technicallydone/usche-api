from rest_framework import serializers

from feedback.enums.question_type import QuestionTypeEnum
from feedback.model.question import Question
from feedback.model.question_option import Option


class FeedbackAnswerItemSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    option_id = serializers.UUIDField(required=False, allow_null=True)
    text = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    def validate(self, attrs):
        question = Question.objects.filter(
            id=attrs["question_id"],
        ).first()

        if question is None:
            raise serializers.ValidationError(
                {
                    "question_id": "Question does not exist."
                }
            )

        option = None

        if attrs.get("option_id"):
            option = Option.objects.filter(
                id=attrs["option_id"],
            ).first()

            if option is None:
                raise serializers.ValidationError(
                    {
                        "option_id": "Selected option does not exist."
                    }
                )

            if option.question_id != question.id:
                raise serializers.ValidationError(
                    {
                        "option_id": (
                            "Selected option does not belong to the selected question."
                        )
                    }
                )

        if question.type == QuestionTypeEnum.MULTIPLE_CHOICE.value:
            if option is None:
                raise serializers.ValidationError(
                    {
                        "option_id": "This question requires an option."
                    }
                )

        if question.type == QuestionTypeEnum.TEXT.value:
            if not attrs.get("text", "").strip():
                raise serializers.ValidationError(
                    {
                        "text": "This question requires text."
                    }
                )

        attrs["question"] = question
        attrs["option"] = option

        return attrs


class SubmitFeedbackSerializer(serializers.Serializer):
    answers = FeedbackAnswerItemSerializer(
        many=True,
        allow_empty=False,
    )