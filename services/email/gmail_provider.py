import logging
from typing import List, Optional, Tuple
from django.core.mail import EmailMessage
from usche_app import settings
from .base import BaseEmailProvider

logger = logging.getLogger(__name__)

class GmailProvider(BaseEmailProvider):
    """
    Email provider using Django's EmailMessage.
    Supports HTML content and attachments.
    """

    def send(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        html_message: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,  # (filename, content, mime_type)
    ) -> None:

        logger.info(
            "Attempting to send email",
            extra={"subject": subject, "recipients": recipients}
        )

        try:
            # Create email message
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )

            # Set HTML content if provided
            if html_message:
                email.content_subtype = "html"
                email.body = html_message

            # Attach files if any
            if attachments:
                for filename, file_content, mime_type in attachments:
                    email.attach(filename, file_content, mime_type)

            # Send email
            email.send(fail_silently=False)

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
