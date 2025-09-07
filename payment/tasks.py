from celery import shared_task
from typing import Dict
import logging
from usche_app import settings
from user.models import User
from utils.beem_sms import BeemSMSClient
from utils.send_email import send_payment_approval_email
from utils.uniode_strip import strip_unicode
from django.db import transaction
from django.core.mail import BadHeaderError

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 5})
def process_payment_approval(self, user_data: Dict):
    sms = BeemSMSClient()

    try:
        with transaction.atomic():
            user = User.objects.filter(user_id=user_data.get('user_id')).first()

            if not user:
                logger.warning(f"User not found for ID: {user_data.get('user_id')}")
                return

            # Send approval email (retry if it fails)
            # try:
            #     send_payment_approval_email(user=user)

            # except BadHeaderError as bhe:
            #     logger.error("BadHeaderError while sending approval email", exc_info=True)

            # except Exception as email_error:
            #     logger.error(f"Failed to send approval email: {email_error}", exc_info=True)
            #     raise self.retry(exc=email_error)

            # Send approval SMS (do not retry if it fails)
            try:
                message = (
                    f"Dear {user.title} {user.last_name},\n\n"
                    f"Your payment has been approved!\n\n"
                    f"Visit your dashboard: {settings.FRONTEND_BASE_URL}/auth\n\n"
                    f"Thank you for joining us!"
                )

                sms_response = sms.send_sms(
                    message=strip_unicode(message),
                    recipients=[user.phone_number]
                )
                logger.info(f"SMS sent successfully to {user.phone_number}: {sms_response}")

            except Exception as sms_error:
                logger.error(f"SMS sending failed: {sms_error}", exc_info=True)
                # Do not retry the whole task for SMS failure

    except Exception as e:
        logger.error("Unexpected failure in process_payment_approval", exc_info=True)
        # Do not raise retry here — only email triggers it
