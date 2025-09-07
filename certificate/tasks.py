from celery import shared_task
from django.db import transaction
from certificate.models import Certificate
from utils.send_email import send_certificate_email
import logging
logger = logging.getLogger(__name__)

@shared_task()
def generate_and_send_certificates_task():
    """
    Generate certificates for all unsent certificates and email them as PDFs.
    """
    try:
        unsent_certificates = Certificate.objects.filter(is_sent=False).select_related('user', 'conference')

        if not unsent_certificates.exists():
            logger.info("No unsent certificates found.")
            return

        for cert in unsent_certificates:
            try:
                
                send_certificate_email(cert=cert)
                
                cert.is_sent = True
                cert.save(update_fields=["is_sent"])

            except Exception as e:
                logger.error(f"Error processing certificate for {cert.user.email}: {str(e)}", exc_info=True)

    except Exception as outer_e:
        logger.error(f"generate_and_send_certificates_task failed: {str(outer_e)}", exc_info=True)
