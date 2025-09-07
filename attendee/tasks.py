from typing import Dict
import uuid
from celery import shared_task
from django.db import transaction
from django.core.mail import BadHeaderError
from attendee.models import Attendee
from utils.send_email import send_qr_code_email
import logging


logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 5})
def process_issue_ticket(self, attendee_id: uuid.UUID):
    try:
        attendee = Attendee.objects.filter(attendee_id=attendee_id).first()
        with transaction.atomic():
            send_qr_code_email(attendee=attendee)

    except Attendee.DoesNotExist:
        logger.error(f"Attendee with ID {attendee_id} does not exist.", exc_info=True)
        return

    except BadHeaderError as bhe:
        logger.error(f"Email sending failed due to BadHeaderError: {str(bhe)}", exc_info=True)
        raise self.retry(exc=bhe)

    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)
