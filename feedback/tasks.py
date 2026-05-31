from celery import shared_task
from django.db import transaction
from django.core.mail import BadHeaderError

from services.email.tasks import send_email_task
from usche_app import settings
from user.models import User
from feedback.models import FeedbackEmailLog
from conference.models import Conference

import logging

logger = logging.getLogger(__name__)


@shared_task()
def request_feedback_task():
    try:
        conference = Conference.get_latest_conference()

        if not conference:
            logger.warning("No conference found, skipping feedback emails.")
            return

        if not conference.is_conference_outdated():
            logger.info(
                f"Conference '{conference.conference_name}' has not ended yet, skipping emails."
            )
            return

        users_to_email = (
            User.objects
            .filter(is_active=True)
            .exclude(
                feedback_emails__conference=conference
            )
        )

        for user in users_to_email:
            try:
                feedback_url = (
                    f"{settings.FRONTEND_BASE_URL}/dashboard/feedback"
                )

                send_email_task.delay(
                    subject=f"Conference Feedback - {conference.conference_name}",
                    to=user.email,
                    greeting=f"Dear {user.first_name},",
                    lines=[
                        (
                            "We would like to express our sincere appreciation "
                            "for your participation in the recent USChE conference."
                        ),
                        (
                            "The conference was a great success, and now we invite "
                            "you to provide your valuable feedback."
                        ),
                        (
                            "Your feedback helps us improve future conferences "
                            "and better serve our participants."
                        ),
                    ],
                    button_text="Submit Feedback",
                    button_url=feedback_url,
                    salutations=[
                        "Thank you for your time and support.",
                        "USChE Team",
                    ],
                    footer_text="© 2026 USChE - University of Dodoma",
                )

                with transaction.atomic():
                    FeedbackEmailLog.objects.create(
                        user=user,
                        conference=conference,
                    )

                logger.info(
                    f"Feedback email queued successfully for {user.email}"
                )

            except BadHeaderError as bhe:
                logger.error(
                    f"Email sending failed for {user.email} due to BadHeaderError: {str(bhe)}",
                    exc_info=True,
                )

            except Exception as e:
                logger.error(
                    f"Email sending failed for {user.email}: {str(e)}",
                    exc_info=True,
                )

    except Exception as outer_e:
        logger.error(
            f"request_feedback_task failed: {str(outer_e)}",
            exc_info=True,
        )
        raise