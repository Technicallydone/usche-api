import uuid
from celery import Task, shared_task
from django.db import transaction
from django.core.mail import BadHeaderError
from services.email.tasks import send_email_task
from usche_app import settings
from user.models import User
import logging

from utils.access_token import generate_token

logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 5})
def process_reset_password_email(self: Task, user_id: uuid.UUID):
    try:
        with transaction.atomic():
            user = User.get_user_by_id(user_id=user_id)
            
            token = generate_token(user=user)
            if not token:
                raise Exception("Failed to generate token")

            # Use the generic send_email_task.delay
            send_email_task.delay(
                subject="Reset Your Password",
                to=user.email,
                greeting=f"Hello {user.first_name},",
                lines=[
                    "We received a request to reset your password.",
                    "Click the button below to set a new password. This link will expire in 24 hours."
                ],
                salutations=["Best regards,", "The USChE Team"],
                button_text="Reset Password",
                button_url=f"{settings.FRONTEND_BASE_URL}/auth/reset-password/{token}",
                footer_text="© 2026 USChE - University of Dodoma"
            )

    except BadHeaderError as bhe:
        logger.error(f"Email sending failed due to BadHeaderError: {str(bhe)}", exc_info=True)
        raise self.retry(exc=bhe)

    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)
