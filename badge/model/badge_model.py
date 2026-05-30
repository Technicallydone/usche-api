import uuid
from django.db import models

from attendee.models import Attendee
from conference.models import Conference


class Badge(models.Model):
    badge_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    attendee = models.OneToOneField(
        Attendee,
        on_delete=models.CASCADE,
        related_name="badge",
    )

    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        related_name="badges",
    )

    qr_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
    )

    generated_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "badges"
        app_label = "badge"

    def __str__(self):
        return (
            f"{self.attendee.participant.full_name} "
            f"- {self.conference.conference_name}"
        )