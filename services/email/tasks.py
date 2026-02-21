# services/email/tasks.py
import logging
from typing import List, Optional
from celery import shared_task, Task

from .mail_template import EmailTemplate

from .gmail_provider import GmailProvider

# Configure logger
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_task(
    self: Task,  # Required for bind=True to use retry
    subject: str,
    to: str,
    greeting: str = "",
    lines: Optional[List[str]] = None,
    salutations: Optional[List[str]] = None,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None,
    footer_text: Optional[str] = None,
    html_message: Optional[str] = None,
) -> None:
    """
    Celery task to send an email using GmailProvider and EmailTemplate.

    :param subject: Email subject
    :param to: Recipient email address
    :param greeting: Greeting text at the top of the email
    :param lines: List of lines for the body of the email
    :param salutations: List of lines for the closing/salutation
    :param button_text: Optional CTA button text
    :param button_url: Optional CTA button URL
    :param footer_text: Optional footer text
    :param html_message: Optional custom HTML content (overrides template)
    :return: None
    """
    lines = lines or []
    salutations = salutations or []

    try:
        # Build the email template if no custom HTML is provided
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

        # Send email using GmailProvider
        provider = GmailProvider()
        provider.send(
            subject=subject,
            message="",  # optional plain text fallback
            recipients=[to],
            html_message=html_message
        )

        # Log success
        logger.info(f"Email successfully sent to {to} with subject '{subject}'")

    except Exception as e:
        # Log error and retry
        logger.error(f"Failed to send email to {to} with subject '{subject}': {e}")
        raise self.retry(exc=e)
