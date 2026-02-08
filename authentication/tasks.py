from typing import Dict
import uuid
import logging

from celery import shared_task, Task
from django.db import transaction
from django.core.mail import BadHeaderError

from usche_app import settings
from user.models import User
from utils.access_token import generate_token
from utils.beem_sms import BeemSMSClient
from utils.send_email import send_activation_email, send_reset_password_email
from utils.uniode_strip import strip_unicode

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 5},
)
def process_reset_password_email(self: Task, user_id: uuid.UUID) -> None:
    """
    Celery task to send reset password email to a user.
    Retries automatically on failure.
    """
    try:
        with transaction.atomic():
            user: User = User.get_user_by_id(user_id=user_id)
            if not user:
                logger.warning(f"No user found with id: {user_id}")
                return

            send_reset_password_email(user=user)

    except BadHeaderError as bhe:
        logger.error(f"Email sending failed due to BadHeaderError: {bhe}", exc_info=True)
        raise self.retry(exc=bhe)

    except Exception as e:
        logger.error(f"Email sending failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 5},
)
def process_registration(self: Task, validated_data: Dict[str, str]) -> None:
    """
    Celery task to process a new user registration:
    - Creates the user
    - Sends activation email
    - Sends SMS notification
    """
    sms = BeemSMSClient()

    try:
        with transaction.atomic():
            user: User = User.create_user(
                title=validated_data.get("title"),
                affiliation=validated_data.get("affiliation"),
                first_name=validated_data.get("first_name"),
                last_name=validated_data.get("last_name"),
                phone_number=validated_data.get("phone_number"),
                email=validated_data.get("email"),
                country=validated_data.get("country"),
                password=validated_data.get("password"),
                middle_name=validated_data.get("middle_name"),
                occupation=validated_data.get("occupation"),
            )

            token: str = generate_token(user=user)

            # send_activation_email(user=user)

            try:
                message: str = (
                    f"Dear {user.title} {user.last_name},\n\n"
                    f"Your registration is successful. Activate your account here:\n\n"
                    f"{settings.FRONTEND_BASE_URL}/activate/{token}"
                )

                sms_response = sms.send_sms(
                    message=strip_unicode(message),
                    recipients=[user.phone_number],
                )
                logger.info(f"SMS sent successfully: {sms_response}")

            except Exception as sms_error:
                logger.error(f"SMS sending failed: {sms_error}", exc_info=True)

    except BadHeaderError as bhe:
        logger.error(f"Email sending failed due to BadHeaderError: {bhe}", exc_info=True)
        raise self.retry(exc=bhe)

    except Exception as e:
        logger.error(f"Registration processing failed: {e}", exc_info=True)
        raise self.retry(exc=e)
