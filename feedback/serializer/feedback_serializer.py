from rest_framework import serializers
from feedback.models import Question, Option

class SingleAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    option_id = serializers.UUIDField(required=False, allow_null=True)
    answer = serializers.CharField(allow_blank=True, required=False)

    def validate(self, data):
        question_id = data.get("question_id")
        answer = data.get("answer", "")
        option_id = data.get("option_id", None)

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            raise serializers.ValidationError("Invalid question ID.")

        data["question"] = question

        if question.type == "multiple-choice":
            if not option_id:
                raise serializers.ValidationError("Option ID is required for multiple-choice questions.")
            try:
                option = Option.objects.get(id=option_id, question=question)
            except Option.DoesNotExist:
                raise serializers.ValidationError("Invalid option for the specified question.")
            data["option"] = option
            data["answer"] = "" 
        elif question.type == "text":
            if not answer:
                raise serializers.ValidationError("Answer is required for text questions.")
            data["option"] = None
        else:
            raise serializers.ValidationError("Unsupported question type.")
        return data
