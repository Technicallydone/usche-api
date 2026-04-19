from django.db import models
from django.utils import timezone
import uuid
from user.models import User
from conference.models import Conference

class FeedbackEmailLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feedback_emails")
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="feedback_email_logs")
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'conference')
        db_table = "feedback_email_logs"
        app_label = "feedback"

    def __str__(self):
        return f"Feedback email sent to {self.user.email} for conference {self.conference.conference_name} at {self.sent_at}"
