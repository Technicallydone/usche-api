from celery import shared_task
from django.db import transaction
from django.core.mail import BadHeaderError
from user.models import User
from feedback.models import FeedbackEmailLog
from utils.email_templates.usche_feedback import usche_feedback_template
from conference.models import Conference
from utils.send_email import send_feedback_email
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
            logger.info(f"Conference '{conference.conference_name}' has not ended yet, skipping emails.")
            return

        # Select active attendees who have NOT received feedback email for this conference
        users_to_email = User.objects.filter(
            is_active=True,
        ).exclude(
            feedback_emails__conference=conference
        )

        for user in users_to_email:
            try:

                send_feedback_email(user=user)

                with transaction.atomic():
                    FeedbackEmailLog.objects.create(user=user, conference=conference)

            except BadHeaderError as bhe:
                logger.error(f"Email sending failed for {user.email} due to BadHeaderError: {str(bhe)}", exc_info=True)
            except Exception as e:
                logger.error(f"Email sending failed for {user.email}: {str(e)}", exc_info=True)

    except Exception as outer_e:
        logger.error(f"request_feedback_task failed: {str(outer_e)}", exc_info=True)
