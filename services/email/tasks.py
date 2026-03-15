import logging
import time
from typing import List, Optional
from celery import shared_task, Task

from .mail_template import EmailTemplate
from .gmail_provider import GmailProvider

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(
    self: Task,
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

    task_id = self.request.id
    start_time = time.monotonic()

    lines = lines or []
    salutations = salutations or []

    logger.info(
        f"Email task started | "
        f"task_id={task_id} | "
        f"recipient={to} | "
        f"subject='{subject}'"
    )

    try:
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

        provider = GmailProvider()

        provider.send(
            subject=subject,
            message="Please view this email in an HTML-compatible client.",
            recipients=[to],
            html_message=html_message,
        )

        duration = round(time.monotonic() - start_time, 3)

        logger.info(
            f"Email sent successfully | "
            f"task_id={task_id} | "
            f"recipient={to} | "
            f"duration={duration}s | "
            f"provider=GmailProvider"
        )

    except Exception as exc:
        duration = round(time.monotonic() - start_time, 3)

        logger.error(
            f"Email sending failed | "
            f"task_id={task_id} | "
            f"recipient={to} | "
            f"duration={duration}s | "
            f"error={str(exc)}"
        )

        raise self.retry(exc=exc)