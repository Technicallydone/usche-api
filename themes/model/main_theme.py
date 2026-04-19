import uuid
from django.db import models

from conference.models import Conference

class MainTheme(models.Model):
    theme_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    conference = models.OneToOneField(
        Conference,
        on_delete=models.CASCADE,
        related_name="theme"
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(null=False)
    
    class Meta:
        db_table = 'main_themes'
        app_label = 'themes'
    
    def __str__(self) -> str:
        return f"{self.title}"
    
    
    @classmethod
    def get_theme_by_conference(cls, conference: Conference):
        return cls.objects.filter(conference=conference).first()
