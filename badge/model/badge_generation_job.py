from celery.result import AsyncResult
from django.utils import timezone
import uuid
from django.db import models
from conference.models import Conference


class BadgeGenerationJob(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    conference = models.OneToOneField(
        Conference,
        on_delete=models.CASCADE,
        related_name="badge_generation_job",
    )

    task_id = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    total_attendees = models.PositiveIntegerField(default=0)
    processed_attendees = models.PositiveIntegerField(default=0)
    successful_badges = models.PositiveIntegerField(default=0)
    failed_badges = models.PositiveIntegerField(default=0)

    zip_file = models.FileField(upload_to="badge-zips/", null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "badge_generation_jobs"
        app_label = "badge"
    
    
    @staticmethod
    def kill_and_delete(conference):
        """
        HARD RESET:
        - stop celery task
        - delete zip file
        - delete DB row
        """

        job = BadgeGenerationJob.objects.filter(conference=conference).first()

        if not job:
            return None

        # 1. stop celery task
        if job.task_id:
            AsyncResult(job.task_id).revoke(terminate=True)

        # 2. delete zip file from storage
        if job.zip_file:
            job.zip_file.delete(save=False)

        # 3. delete DB row
        job.delete()

        return True