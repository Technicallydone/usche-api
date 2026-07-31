import uuid

from django.db import models

from conference.models import Conference
from feedback.enums.question_type import QuestionTypeEnum


class Question(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    conference = models.ForeignKey(
        Conference,
        related_name="questions",
        on_delete=models.CASCADE,
        db_index=True,
    )

    question = models.TextField()

    type = models.CharField(
        max_length=100,
        choices=QuestionTypeEnum.choices(),
        default=QuestionTypeEnum.default(),
        db_index=True,
    )

    is_required = models.BooleanField(default=True)

    position = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"
        app_label = "feedback"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["conference", "position"],
                name="unique_question_position_per_conference",
            )
        ]

    def __str__(self):
        return self.question