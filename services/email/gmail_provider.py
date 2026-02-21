import logging
from typing import List
from django.core.mail import send_mail
from .base import BaseEmailProvider
from usche_app import settings

logger = logging.getLogger(__name__)

class GmailProvider(BaseEmailProvider):

    def send(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        html_message: str | None = None
    ) -> None:

        logger.info(
            "Attempting to send email",
            extra={"subject": subject, "recipients": recipients}
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
                html_message=html_message,
            )

            logger.info(
                "Email sent successfully",
                extra={"subject": subject, "recipients": recipients}
            )

        except Exception as e:
            logger.exception(
                "Failed to send email",
                extra={"subject": subject, "recipients": recipients, "error": str(e)}
            )
            raise
