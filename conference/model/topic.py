import uuid
from django.db import models

from conference.model.conference import Conference


class Topic(models.Model):
    topic_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="topics")
    topic_name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    
    class Meta:
        db_table = 'topics'
        app_label = 'conference'