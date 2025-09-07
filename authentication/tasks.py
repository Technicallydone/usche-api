import uuid
from celery import shared_task
from django.db import transaction
from django.core.mail import BadHeaderError
from user.models import User
from utils.send_email import send_reset_password_email
import logging



logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 5})
def process_reset_password_email(self, user_id: uuid.UUID):
    try:
        with transaction.atomic():
            user = User.get_user_by_id(user_id=user_id)
            send_reset_password_email(user=user)

    except BadHeaderError as bhe:
        logger.error(f"Email sending failed due to BadHeaderError: {str(bhe)}", exc_info=True)
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)