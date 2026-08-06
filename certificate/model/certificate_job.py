import uuid
from django.db import models
from django.utils import timezone
from conference.models import Conference


class CertificateGenerationJob(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.OneToOneField(
        Conference,
        on_delete=models.CASCADE,
        related_name="certificate_generation_job",
    )
    task_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_attendees = models.PositiveIntegerField(default=0)
    processed_attendees = models.PositiveIntegerField(default=0)
    successful_certificates = models.PositiveIntegerField(default=0)
    failed_certificates = models.PositiveIntegerField(default=0)

    zip_file = models.FileField(upload_to="certificates/zips/", null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "certificate_generation_jobs"
        app_label = "certificate"

    def __str__(self):
        return f"Certificate Job for {self.conference.conference_name} - {self.status}"

    @classmethod
    def kill_and_delete(cls, conference: Conference):
        """
        Revokes running Celery task (if any) and deletes existing job for the conference.
        """
        try:
            job = cls.objects.get(conference=conference)
            if job.task_id:
                from usche_app.celery import app

                app.control.revoke(job.task_id, terminate=True)
            job.delete()
        except cls.DoesNotExist:
            pass