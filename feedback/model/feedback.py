import uuid
from django.db import models
from feedback.model.question import Question
from feedback.model.question_option import Option

class FeedbackAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    option = models.ForeignKey(Option, null=True, blank=True, on_delete=models.SET_NULL)
    text = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.question.id}"

    class Meta:
        db_table = "feedbacks"
        app_label = "feedback"
