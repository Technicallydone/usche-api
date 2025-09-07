import uuid
from django.db import models

from feedback.model.question import Question

class Option(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, related_name="options", on_delete=models.CASCADE)
    option = models.CharField(max_length=255) 

    def __str__(self):
        return f"{self.option}"
    
    class Meta:
        db_table = 'question_option'
        app_label = 'feedback'