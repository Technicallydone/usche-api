import logging
from typing import List, Optional, Dict
from celery import shared_task, Task
from .gmail_provider import GmailProvider
from .mail_template import EmailTemplate

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_task(
    self: Task,  # Required for bind=True
    subject: str,
    to: str,
    greeting: str = "",
    lines: Optional[List[str]] = None,
    salutations: Optional[List[str]] = None,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None,
    footer_text: Optional[str] = None,
    html_message: Optional[str] = None,
    attachments: Optional[List[Dict]] = None,  # {"filename": str, "content": bytes, "mime_type": str}
) -> None:
    """
    Celery task to send an email using GmailProvider and EmailTemplate.
    Supports attachments.
    """
    lines = lines or []
    salutations = salutations or []

    try:
        # Build HTML template if not provided
        if not html_message:
            template = EmailTemplate(subject=subject, to=to)
            if greeting:
                template.set_greeting(greeting)
            if lines:
                template.add_lines(lines)
            if salutations:
                template.add_salutations(salutations)
            if button_text and button_url:
                template.set_button(button_text, button_url)
            if footer_text:
                template.set_footer(footer_text)

            html_message = template.build()

        # Prepare attachments for GmailProvider
        formatted_attachments = None
        if attachments:
            formatted_attachments = [
                (att["filename"], att["content"], att["mime_type"]) for att in attachments
            ]

        # Send email
        provider = GmailProvider()
        provider.send(
            subject=subject,
            message="",  # optional plain text fallback
            recipients=[to],
            html_message=html_message,
            attachments=formatted_attachments
        )

        logger.info(f"Email successfully sent to {to} with subject '{subject}'")

    except Exception as e:
        logger.error(f"Failed to send email to {to} with subject '{subject}': {e}")
        raise self.retry(exc=e)
