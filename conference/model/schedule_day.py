import uuid
from django.db import models
from conference.model.conference import Conference

class ScheduleDay(models.Model):
    schedule_day_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="schedule_days")
    date = models.DateField()
    title = models.CharField(max_length=255, help_text="Day Two: 12th June 2025")
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "schedule_day"
        app_label = "conference"
        ordering = ["date"]

    def __str__(self):
        return f"{self.conference.conference_name} - {self.title}"
    
    @classmethod
    def get_by_conference(cls, conference: Conference):
        return cls.objects.filter(conference=conference).order_by('date')