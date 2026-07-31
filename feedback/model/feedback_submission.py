import uuid

from django.db import models

from conference.models import Conference


class FeedbackSubmission(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    conference = models.ForeignKey(
        Conference,
        related_name="feedback_submissions",
        on_delete=models.CASCADE,
        db_index=True,
    )

    email = models.EmailField(
        db_index=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "feedback_submissions"
        app_label = "feedback"
        ordering = ["-submitted_at"]

    def __str__(self):
        return self.email