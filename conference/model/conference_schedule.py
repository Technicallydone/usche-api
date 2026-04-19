from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from conference.enum.session_type import SessionTypeEnum
from conference.model.schedule_day import ScheduleDay

class ConferenceSchedule(models.Model):
    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule_day = models.ForeignKey(ScheduleDay, on_delete=models.CASCADE, related_name="schedules")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    activity = models.TextField(default="")
    speaker = models.CharField(max_length=255, blank=True)
    moderator = models.CharField(max_length=255, blank=True)
    hall = models.CharField(max_length=100, blank=True)
    session_type = models.CharField(
        max_length=20,
        choices=SessionTypeEnum.choices(),
        default=SessionTypeEnum.default()
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conference_scheduls"
        app_label = "conference"
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.schedule_day.title} - {self.date}: {self.activity[:50]}"

    def clean(self):
        """Ensure that the schedule date is within the conference day date."""
        if self.date != self.schedule_day.date:
            raise ValidationError("Schedule date must match the associated schedule day date.")

        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")
