from rest_framework import serializers


class OptionCountSerializer(serializers.Serializer):
    option_id = serializers.UUIDField()
    option_text = serializers.CharField()
    count = serializers.IntegerField()


class TextAnswerSerializer(serializers.Serializer):
    text = serializers.CharField()
    submitted_at = serializers.DateTimeField()


class QuestionReportSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    question_text = serializers.CharField()
    type = serializers.CharField()
    options = OptionCountSerializer(many=True, required=False)
    answers = TextAnswerSerializer(many=True, required=False)
