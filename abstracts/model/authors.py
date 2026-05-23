import uuid
from django.db import models
from abstracts.model.abstract import Abstract

class AbstractAuthor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    abstract = models.ForeignKey(Abstract, on_delete=models.CASCADE, related_name="authors")

    full_name = models.CharField(max_length=255)
    affiliation = models.CharField(max_length=255)

    is_presenting_author = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "abstract_authors"
        app_label = 'abstracts'
        ordering = ["order"]
        
    def __str__(self):
        return self.full_name