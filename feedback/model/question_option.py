import uuid

from django.db import models

from feedback.model.question import Question


class Option(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    question = models.ForeignKey(
        Question,
        related_name="options",
        on_delete=models.CASCADE,
        db_index=True,
    )

    option = models.CharField(max_length=255)

    position = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "question_options"
        app_label = "feedback"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "position"],
                name="unique_option_position_per_question",
            ),
            models.UniqueConstraint(
                fields=["question", "option"],
                name="unique_option_per_question",
            ),
        ]

    def __str__(self):
        return self.option