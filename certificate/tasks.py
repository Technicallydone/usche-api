from celery import shared_task
from abstracts.models import Abstract
from certificate.enums.cert_purpose import CertificatePurpose
from certificate.models import Certificate, CertificateZip
from conference.models import Conference
from usche_app import settings
from utils.document_generator import generate_certificate_pdf
from django.utils import timezone
from pathlib import Path
import zipfile, io, logging

logger = logging.getLogger(__name__)

@shared_task()
def generate_certificates_for_conference_task():
    """
    Generate attendance and presentation certificates for all users without certificates
    for the given conference and append them to the conference ZIP.
    If a certificate filename already exists in the ZIP, append an index to avoid duplicates.
    """
    try:
        conference = Conference.get_latest_conference()
        users = Certificate.users_without_certificate_for_conference(conference)
        batch_time = timezone.now()

        if not users.exists():
            logger.info(f"No new users without certificates for conference {conference.conference_id}")
            return {"status": "success", "message": "No new users to process"}

        cert_zip_obj, _ = CertificateZip.objects.get_or_create(conference=conference)
        zip_path = (
            Path(cert_zip_obj.zip_file.path)
            if cert_zip_obj.zip_file
            else Path(settings.MEDIA_ROOT) / "certificates" / f"{conference.conference_id}.zip"
        )
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare in-memory buffer for new files
        new_buffer = io.BytesIO()
        with zipfile.ZipFile(new_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, u in enumerate(users, start=1):
                # Attendance certificate
                Certificate.objects.create(
                    user=u,
                    conference=conference,
                    is_created=True,
                    issued_at=batch_time
                )
                pdf_bytes = generate_certificate_pdf(user=u, conference=conference, purpose=CertificatePurpose.ATTENDANCE.value)
                if pdf_bytes:
                    filename = f"{u.first_name}_{u.last_name}__attendance_certificate.pdf"
                    # Append index if duplicate in this batch
                    if filename in zip_file.namelist():
                        filename = f"{u.first_name}_{u.last_name}__attendance_certificate_{idx}.pdf"
                    zip_file.writestr(filename, pdf_bytes)

                # Presentation certificate
                abstracts = Abstract.objects.filter(
                    user=u,
                    sub_theme__theme__conference__conference_id=conference.conference_id
                )
                if abstracts.exists():
                    Certificate.objects.create(
                        user=u,
                        conference=conference,
                        is_created=True,
                        issued_at=batch_time
                    )
                    pdf_bytes_pres = generate_certificate_pdf(user=u, conference=conference, purpose=CertificatePurpose.PRESENTATION.value)
                    if pdf_bytes_pres:
                        filename_pres = f"{u.first_name}_{u.last_name}__presentation_certificate.pdf"
                        if filename_pres in zip_file.namelist():
                            filename_pres = f"{u.first_name}_{u.last_name}__presentation_certificate_{idx}.pdf"
                        zip_file.writestr(filename_pres, pdf_bytes_pres)

        # Append new_buffer to existing ZIP if it exists
        if zip_path.exists():
            with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as existing_zip:
                existing_filenames = {f.filename for f in existing_zip.infolist()}
                with zipfile.ZipFile(new_buffer, "r") as new_zip:
                    for file_info in new_zip.infolist():
                        filename = file_info.filename
                        # Append index if filename already exists in existing ZIP
                        counter = 1
                        while filename in existing_filenames:
                            name_parts = file_info.filename.rsplit('.', 1)
                            filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                            counter += 1
                        existing_zip.writestr(filename, new_zip.read(file_info.filename))
                        existing_filenames.add(filename)
        else:
            # If ZIP doesn't exist, write the new buffer directly
            with open(zip_path, "wb") as f:
                f.write(new_buffer.getvalue())

        # Update DB
        cert_zip_obj.zip_file.name = str(zip_path.relative_to(Path("media")))
        cert_zip_obj.save(update_fields=["zip_file", "updated_at"])

        return {"status": "success", "zip_path": cert_zip_obj.zip_file.url}

    except Conference.DoesNotExist:
        logger.error(f"Conference {conference.conference_id} does not exist")
        return {"status": "failed", "error": f"Conference {conference.conference_id} not found"}
    except Exception as e:
        logger.error(f"Error generating certificates for conference {conference.conference_id}: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
