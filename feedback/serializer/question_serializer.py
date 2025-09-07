from rest_framework import serializers
from feedback.models import Question, Option
from feedback.serializer.option_serializer import OptionSerializer


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question', 'type', 'conference', 'options']
