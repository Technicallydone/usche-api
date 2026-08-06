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


class OptionReportSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    option = serializers.CharField(read_only=True)
    position = serializers.IntegerField(read_only=True)
    count = serializers.IntegerField(read_only=True, default=0)
    percentage = serializers.FloatField(read_only=True, default=0.0)


class QuestionReportSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    question = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    is_required = serializers.BooleanField(read_only=True)
    position = serializers.IntegerField(read_only=True)
    total_responses = serializers.IntegerField(read_only=True, default=0)
    options = OptionReportSerializer(many=True, read_only=True, default=[])
    text_responses = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        default=[],
    )

    def to_representation(self, instance: Question):
        answers = instance.answers.all()
        total_responses = answers.count()

        data = {
            "id": instance.id,
            "question": instance.question,
            "type": instance.type,
            "is_required": instance.is_required,
            "position": instance.position,
            "total_responses": total_responses,
        }

        if instance.type == QuestionTypeEnum.MULTIPLE_CHOICE.value:
            options_data = []
            for option in instance.options.all():
                option_count = answers.filter(option=option).count()
                percentage = (
                    round((option_count / total_responses) * 100, 2)
                    if total_responses > 0
                    else 0.0
                )

                options_data.append(
                    {
                        "id": option.id,
                        "option": option.option,
                        "position": option.position,
                        "count": option_count,
                        "percentage": percentage,
                    }
                )

            data["options"] = options_data
            data["text_responses"] = []
        else:
            data["options"] = []
            data["text_responses"] = list(
                answers.exclude(text="").values_list("text", flat=True)
            )

        return data


class FeedbackAnswerDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    question_id = serializers.UUIDField(read_only=True, source="question.id")
    question_text = serializers.CharField(read_only=True, source="question.question")
    question_type = serializers.CharField(read_only=True, source="question.type")
    option_id = serializers.UUIDField(
        read_only=True, source="option.id", allow_null=True
    )
    option_text = serializers.CharField(
        read_only=True, source="option.option", allow_null=True
    )
    text = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, source="submitted_at")


class FeedbackReportFilterQuerySerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=False, allow_null=True)
    created_from = serializers.DateTimeField(required=False, allow_null=True)
    created_to = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        created_from = attrs.get("created_from")
        created_to = attrs.get("created_to")

        if created_from and created_to and created_from > created_to:
            raise serializers.ValidationError(
                {"created_from": "'created_from' must be earlier than 'created_to'."}
            )

        return attrs