from django.db import models

from conference.models import Conference
from utils.upload_document_to import upload_certificate_zip


class CertificateZip(models.Model):
    """
    Tracks the ZIP file for each conference.
    """
    conference = models.OneToOneField(
        Conference,
        on_delete=models.CASCADE,
        related_name="certificate_zip"
    )
    zip_file = models.FileField(upload_to=upload_certificate_zip, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'certificate_zips'
        app_label = 'certificate'

    def __str__(self):
        return f"Certificate ZIP for {self.conference.conference_name}"