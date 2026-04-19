# models/conference_document.py
import uuid
from django.db import models
from conference.model.conference import Conference
from utils.upload_document_to import upload_schedule_document
from utils.validator import validate_pdf_document


class ConferenceScheduleDocument(models.Model):
    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=upload_schedule_document, validators=[validate_pdf_document])
    is_active = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conference_schedule_documents'
        app_label = 'conference'

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"
