import io
import logging
from pathlib import Path
import zipfile

from celery import Task, shared_task
from django.core.files import File
from django.db import transaction
from django.utils import timezone

from abstracts.models import Abstract
from certificate.enums.cert_purpose import CertificatePurpose
from certificate.models import Certificate, CertificateGenerationJob, CertificateZip
from usche_app import settings
from utils.document_generator import generate_certificate_pdf

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 5},
)
def generate_conference_certificates_task(self: Task, job_id: str):
    """
    Generates attendance and presentation certificates for all users without certificates
    in a conference, tracks progress on CertificateGenerationJob, and updates CertificateZip.
    """
    try:
        job = CertificateGenerationJob.objects.select_related("conference").get(
            job_id=job_id
        )
        conference = job.conference

        # Fetch eligible users using claim_users_for_certificates or queryset
        users = Certificate.users_without_certificate_for_conference(
            conference=conference
        ).order_by("created_at")

        total_users = users.count()

        job.status = CertificateGenerationJob.Status.RUNNING
        job.started_at = timezone.now()
        job.total_attendees = total_users
        job.processed_attendees = 0
        job.successful_certificates = 0
        job.failed_certificates = 0
        job.save()

        logger.info(
            f"Starting certificate generation for conference '{conference.conference_name}'"
        )

        zip_buffer = io.BytesIO()
        batch_time = timezone.now()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, user in enumerate(users, start=1):
                try:
                    user_has_success = False

                    # ---------- Attendance Certificate ----------
                    try:
                        with transaction.atomic():
                            Certificate.objects.create(
                                user=user,
                                conference=conference,
                                is_created=True,
                                issued_at=batch_time,
                            )

                        pdf_bytes = generate_certificate_pdf(
                            user=user,
                            conference=conference,
                            purpose=CertificatePurpose.ATTENDANCE,
                        )

                        if pdf_bytes:
                            filename = f"attendance/{user.first_name}_{user.last_name}.pdf"
                            if filename in zip_file.namelist():
                                filename = (
                                    f"attendance/{user.first_name}_{user.last_name}_{idx}.pdf"
                                )
                            zip_file.writestr(filename, pdf_bytes)
                            user_has_success = True

                    except Exception as cert_err:
                        logger.error(
                            f"Attendance certificate failed for user {user.id}: {cert_err}",
                            exc_info=True,
                        )

                    # ---------- Presentation Certificate ----------
                    abstracts = Abstract.objects.filter(
                        user=user,
                        sub_theme__theme__conference__conference_id=conference.conference_id,
                    )

                    if abstracts.exists():
                        try:
                            with transaction.atomic():
                                Certificate.objects.create(
                                    user=user,
                                    conference=conference,
                                    is_created=True,
                                    issued_at=batch_time,
                                )

                            pdf_bytes_pres = generate_certificate_pdf(
                                user=user,
                                conference=conference,
                                purpose=CertificatePurpose.PRESENTATION,
                            )

                            if pdf_bytes_pres:
                                filename_pres = (
                                    f"presentation/{user.first_name}_{user.last_name}.pdf"
                                )
                                if filename_pres in zip_file.namelist():
                                    filename_pres = f"presentation/{user.first_name}_{user.last_name}_{idx}.pdf"
                                zip_file.writestr(filename_pres, pdf_bytes_pres)
                                user_has_success = True

                        except Exception as pres_err:
                            logger.error(
                                f"Presentation certificate failed for user {user.id}: {pres_err}",
                                exc_info=True,
                            )

                    if user_has_success:
                        job.successful_certificates += 1
                    else:
                        job.failed_certificates += 1

                except Exception as user_error:
                    logger.error(
                        f"Failed certificate generation flow for user {user.id}: {user_error}",
                        exc_info=True,
                    )
                    job.failed_certificates += 1

                finally:
                    job.processed_attendees += 1

                    CertificateGenerationJob.objects.filter(pk=job.pk).update(
                        processed_attendees=job.processed_attendees,
                        successful_certificates=job.successful_certificates,
                        failed_certificates=job.failed_certificates,
                    )

        zip_buffer.seek(0)

        # Save to disk
        zip_dir = Path(settings.MEDIA_ROOT) / "certificate-zips"
        zip_dir.mkdir(parents=True, exist_ok=True)

        filename = f"certificates_{conference.conference_id}.zip"
        zip_path = zip_dir / filename

        with open(zip_path, "wb") as f:
            f.write(zip_buffer.getvalue())

        # Save to Job
        with open(zip_path, "rb") as f:
            job.zip_file.save(filename, File(f), save=False)

        job.status = CertificateGenerationJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.save()

        # Save or update CertificateZip record for listing in table
        cert_zip_obj, _ = CertificateZip.objects.get_or_create(conference=conference)
        with open(zip_path, "rb") as f:
            cert_zip_obj.zip_file.save(filename, File(f), save=True)

        logger.info(
            f"Certificate generation completed for {conference.conference_name}"
        )

        return {
            "status": "success",
            "job_id": str(job.job_id),
            "successful": job.successful_certificates,
            "failed": job.failed_certificates,
        }

    except Exception as e:
        logger.error(f"Certificate generation failed: {e}", exc_info=True)

        CertificateGenerationJob.objects.filter(job_id=job_id).update(
            status=CertificateGenerationJob.Status.FAILED,
            completed_at=timezone.now(),
        )

        raise self.retry(exc=e)