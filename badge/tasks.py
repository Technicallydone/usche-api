# badge/tasks.py

import io
import zipfile
import logging

from pathlib import Path

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.files import File

from attendee.models import Attendee
from badge.models import Badge, BadgeGenerationJob
from usche_app import settings
from utils.document_generator import generate_badge_pdf

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 5},
)
def generate_conference_badges_task(self, job_id: str):
    """
    Generates badges for all attendees in a conference
    and stores them in a single ZIP file.
    """

    try:
        job = BadgeGenerationJob.objects.select_related(
            "conference"
        ).get(job_id=job_id)

        conference = job.conference

        attendees = (
            Attendee.objects
            .select_related("participant")
            .filter(conference=conference)
            .order_by("created_at")
        )

        total_attendees = attendees.count()

        job.status = BadgeGenerationJob.Status.RUNNING
        job.started_at = timezone.now()
        job.total_attendees = total_attendees
        job.processed_attendees = 0
        job.successful_badges = 0
        job.failed_badges = 0
        job.save()

        logger.info(
            f"Starting badge generation for {conference.conference_name}"
        )

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as zip_file:

            for attendee in attendees:

                try:
                    with transaction.atomic():

                        badge, _ = Badge.objects.get_or_create(
                            attendee=attendee,
                            conference=conference,
                        )

                    pdf_bytes = generate_badge_pdf(
                        user=attendee.participant,
                        conference=conference,
                    )

                    if not pdf_bytes:
                        raise Exception("Badge PDF generation failed")

                    participant = attendee.participant

                    filename = (
                        f"{participant.first_name}_{participant.last_name}.pdf"
                    )

                    zip_file.writestr(filename, pdf_bytes)

                    job.successful_badges += 1

                except Exception as attendee_error:

                    logger.error(
                        f"Failed badge generation for attendee "
                        f"{attendee.attendee_id}: {attendee_error}",
                        exc_info=True,
                    )

                    job.failed_badges += 1

                finally:

                    job.processed_attendees += 1

                    BadgeGenerationJob.objects.filter(
                        pk=job.pk
                    ).update(
                        processed_attendees=job.processed_attendees,
                        successful_badges=job.successful_badges,
                        failed_badges=job.failed_badges,
                    )

        zip_buffer.seek(0)

        zip_dir = Path(settings.MEDIA_ROOT) / "badge-zips"
        zip_dir.mkdir(parents=True, exist_ok=True)

        filename = f"badges_{conference.conference_id}.zip"
        zip_path = zip_dir / filename

        with open(zip_path, "wb") as f:
            f.write(zip_buffer.getvalue())

        with open(zip_path, "rb") as f:
            job.zip_file.save(
                filename,
                File(f),
                save=False,
            )

        job.status = BadgeGenerationJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.save()

        logger.info(
            f"Badge generation completed for {conference.conference_name}"
        )

        return {
            "status": "success",
            "job_id": str(job.job_id),
            "successful": job.successful_badges,
            "failed": job.failed_badges,
        }

    except Exception as e:

        logger.error(
            f"Badge generation failed: {e}",
            exc_info=True,
        )

        BadgeGenerationJob.objects.filter(
            job_id=job_id
        ).update(
            status=BadgeGenerationJob.Status.FAILED,
            completed_at=timezone.now(),
        )

        raise self.retry(exc=e)