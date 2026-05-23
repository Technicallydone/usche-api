import logging
from typing import List, Optional, Dict, Any

from django.core.mail import EmailMessage
from django.conf import settings

from .base import BaseEmailProvider

logger = logging.getLogger(__name__)


class GmailProvider(BaseEmailProvider):

    def send(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        html_message: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:

        attachments = attachments or []

        logger.info(
            "Attempting to send email",
            extra={"subject": subject, "recipients": recipients, "attachments": len(attachments)},
        )

        try:
            # -----------------------------------
            # SWITCH TO EmailMessage (NOT send_mail)
            # -----------------------------------
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )

            # HTML support
            if html_message:
                email.content_subtype = "html"
                email.body = html_message

            # -----------------------------------
            # ATTACHMENTS SUPPORT
            # -----------------------------------
            for att in attachments:
                email.attach(
                    att["filename"],
                    att["content"],
                    att["mime_type"],
                )

            email.send(fail_silently=False)

            logger.info(
                "Email sent successfully",
                extra={
                    "subject": subject,
                    "recipients": recipients,
                    "attachments": len(attachments),
                },
            )

        except Exception as e:
            logger.exception(
                "Failed to send email",
                extra={
                    "subject": subject,
                    "recipients": recipients,
                    "error": str(e),
                },
            )
            raise