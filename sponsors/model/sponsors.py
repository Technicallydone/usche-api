import uuid
from django.db import models

from conference.models import Conference
from utils.image_validator import validate_image
from utils.upload_image import upload_sponsor_logo_to

class Sponsor(models.Model):
    sponsor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="sponsors")
    name = models.CharField(max_length=255, null=False, blank=False, help_text="Name of the sponsor.")
    logo = models.ImageField(upload_to=upload_sponsor_logo_to, validators=[validate_image], null=True, blank=True, help_text="Logo of the sponsor.")
    website = models.URLField(null=True, blank=True, help_text="Sponsor's website URL.")
    contact_email = models.EmailField(null=True, blank=True, help_text="Sponsor's contact email.")
    priority = models.IntegerField(unique=False, help_text="Priority of the sponsor (higher number means higher priority).")
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sponsors'
        app_label = 'sponsors'
        ordering = ['-priority']