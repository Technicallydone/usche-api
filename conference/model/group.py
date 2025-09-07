import uuid
from django.db import models

from conference.model.conference import Conference


class TargetGroup(models.Model):
    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="groups")
    group_name = models.CharField(max_length=255, null=False, blank=False)
    
    class Meta:
        db_table = 'target_group'
        app_label = 'conference'
        
        
    @classmethod
    def total_conference_target_groups(cls, conference: Conference) -> int:
        return cls.objects.filter(conference=conference).count()