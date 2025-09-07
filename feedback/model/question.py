import uuid
from django.db import models

from conference.models import Conference
from feedback.enums.question_type import QuestionTypeEnum

class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.ForeignKey(Conference, related_name="questions", on_delete=models.CASCADE)
    question = models.TextField()
    type = models.CharField(
        max_length=100,
        choices=QuestionTypeEnum.choices(),
        default=QuestionTypeEnum.default()
    )

    def __str__(self):
        return f"{self.question} ({self.conference.conference_name})"
    
    class Meta:
        db_table = 'question'
        app_label = 'feedback'