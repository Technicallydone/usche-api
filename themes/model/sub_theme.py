import uuid
from django.db import models

from themes.model.main_theme import MainTheme

class SubTheme(models.Model):
    sub_theme_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme = models.ForeignKey(MainTheme, on_delete=models.CASCADE, related_name="sub_themes")
    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    
    class Meta:
        db_table = 'sub_themes'
        app_label = 'themes'
        
    def __str__(self) -> str:
        return f"{self.title}"
    
    @classmethod
    def get_sub_theme_by_id(cls, sub_theme_id: uuid.UUID):
        return cls.objects.filter(sub_theme_id=sub_theme_id).first()
    
    @classmethod
    def get_total_theme_subthemes(cls, theme: MainTheme) -> int:
        return cls.objects.filter(theme=theme).count()