import uuid

from django.core.exceptions import ValidationError
from django.db import models

from feedback.model.question import Question
from feedback.model.question_option import Option


class FeedbackAnswer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    question = models.ForeignKey(
        Question,
        related_name="answers",
        on_delete=models.PROTECT,
        db_index=True,
    )

    option = models.ForeignKey(
        Option,
        related_name="answers",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    text = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feedback_answers"
        app_label = "feedback"
        ordering = ["submitted_at"]

    def clean(self):
        if self.option and self.option.question != self.question:
            raise ValidationError(
                {"option": "Selected option does not belong to the selected question."}
            )

    def __str__(self):
        return f"Answer for '{self.question.question[:40]}'"