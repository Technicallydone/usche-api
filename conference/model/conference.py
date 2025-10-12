import uuid
from django.db import models
from django.db.models import Q
from django.utils import timezone
from utils.upload_document_to import upload_certificate_template
from utils.validator import validate_future_date

class Conference(models.Model):
    conference_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference_name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    start_date = models.DateField(blank=False, validators=[validate_future_date])
    end_date = models.DateField(blank=False, validators=[validate_future_date])
    start_time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)
    venue_name = models.CharField(max_length=255, null=False, blank=False)
    venue_website = models.URLField(null=True, blank=True)
    venue_description = models.TextField(null=False, blank=False)
    venue_directions = models.TextField(null=True, blank=True)
    capacity = models.IntegerField(null=False, blank=False)

    abstract_submission_deadline = models.DateTimeField(null=False, blank=False)
    
    certificate_background = models.FileField(
        upload_to=upload_certificate_template,
        null=True,
        blank=True,
        help_text="Upload the SVG or image file used as the certificate background"
    )

    
    registration_open = models.BooleanField(default=False)
    
    year = models.CharField(blank=False, null=False, default='2025')

    listing_date = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        db_table = 'conference'
        app_label = 'conference'
        
    def __str__(self) -> str:
        return f"{self.conference_name}"
    
    @classmethod
    def get_conference_by_id(cls, conference_id: uuid.UUID):
        return cls.objects.filter(conference_id=conference_id).first()

    def is_abstract_submission_deadline_reached(self) -> bool:
        return timezone.now() > self.abstract_submission_deadline

    def is_conference_outdated(self) -> bool:
        return timezone.now().date() > self.end_date
    
    @classmethod
    def get_latest_conference(cls):
        return cls.objects.order_by('-listing_date').first()
    
    @classmethod
    def get_conference(cls, year: str = None):
        if (year):
            return cls.objects.filter(year=year).first()
        
        return cls.objects.order_by('-listing_date').first()