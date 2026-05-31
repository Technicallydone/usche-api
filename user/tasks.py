from datetime import timedelta
from celery import shared_task
from django.db import transaction
from django.core.mail import BadHeaderError
from conference.model import Conference
from invitation.models import Invitation
from services.email.tasks import send_email_task
from usche_app import settings
from user.models import User
import logging
from django.utils.timezone import now
from django.utils import timezone
from utils.access_token import generate_token



logger = logging.getLogger(__name__)

@shared_task()
def send_low_priority_email():
    try:
        with transaction.atomic():
            ten_minutes_ago = now() - timedelta(minutes=10)

            user = (
                User.objects
                .filter(
                    created_at__lte=ten_minutes_ago,
                    is_active=False,
                    has_sent_activation_email=False,
                )
                .order_by("-created_at")
                .first()
            )

            if not user:
                logger.info("No pending activation emails found.")
                return

            token = generate_token(user=user)
            activation_url = f"{settings.FRONTEND_BASE_URL}/activate/{token}"

            send_email_task.delay(
                subject="Activate Your Account - USChE",
                to=user.email,
                greeting=f"Hello {user.first_name},",
                lines=[
                    "Your registration is successful.",
                    "Please activate your account using the button below.",
                    "This activation link will expire in 1 hour.",
                    "If you did not create this account, please ignore this email.",
                ],
                button_text="Activate Account",
                button_url=activation_url,
                salutations=[
                    "Best regards,",
                    "USChE Team",
                ],
                footer_text="© 2026 USChE - University of Dodoma",
            )

            user.has_sent_activation_email = True
            user.save(update_fields=["has_sent_activation_email"])

            logger.info(
                f"Activation email queued successfully for {user.email}"
            )

    except BadHeaderError as bhe:
        logger.error(
            f"Email sending failed due to BadHeaderError: {str(bhe)}",
            exc_info=True,
        )

    except Exception as e:
        logger.error(
            f"Email sending failed: {str(e)}",
            exc_info=True,
        )
        raise
        

@shared_task()
def send_high_priority_email():
    try:
        with transaction.atomic():

            user = (
                User.objects
                .filter(is_active=False, resend_activation_email=True)
                .order_by('-created_at')
                .first()
            )

            if not user:
                logger.info("No pending activation emails found.")
                return

            # -----------------------------------
            # LOCK / MARK AS PROCESSED
            # -----------------------------------
            user.resend_activation_email = False
            user.save(update_fields=['resend_activation_email'])

            token = generate_token(user=user)
            activation_url = f"{settings.FRONTEND_BASE_URL}/activate/{token}"

            # -----------------------------------
            # SEND EMAIL (NEW SYSTEM)
            # -----------------------------------
            send_email_task.delay(
                subject="Activate Your Account - USChE",
                to=user.email,
                greeting=f"Hello {user.first_name},",
                lines=[
                    "Your registration is successful.",
                    "Please activate your account using the button below.",
                ],
                button_text="Activate Account",
                button_url=activation_url,
                salutations=[
                    "Best regards,",
                    "USChE Team"
                ],
                footer_text="© 2026 USChE - University of Dodoma",
            )

    except Exception as e:
        logger.error(
            f"High priority email task failed: {str(e)}",
            exc_info=True
        )
        raise
        
    
@shared_task
def send_deadline_reminder_high_priority_email():
    try:
        with transaction.atomic():
            conference = Conference.get_latest_conference()

            if not conference:
                return

            if conference.is_conference_outdated():
                return

            abstract_submission_deadline = (
                conference.abstract_submission_deadline
            )

            now = timezone.now()

            days_until_deadline = (
                abstract_submission_deadline.date() - now.date()
            ).days

            if not 0 <= days_until_deadline <= 14:
                return

            users_to_remind = (
                Invitation.objects
                .filter(
                    conference=conference,
                    user__abstracts__isnull=True,
                )
                .values_list("user", flat=True)
                .distinct()
            )

            users_to_notify = (
                User.objects
                .filter(user_id__in=users_to_remind)
                .distinct()
            )

            if not users_to_notify.exists():
                logger.info("No users require abstract deadline reminders.")
                return

            abstract_url = (
                f"{settings.FRONTEND_BASE_URL}/dashboard/abstract"
            )

            for user in users_to_notify:
                logger.info(
                    f"Queueing abstract reminder email to: {user.email}"
                )

                send_email_task.delay(
                    subject=(
                        f"Abstract Submission Reminder - "
                        f"{conference.conference_name}"
                    ),
                    to=user.email,
                    greeting=(
                        f"Dear {user.title or ''} "
                        f"{user.last_name},"
                    ).strip(),
                    lines=[
                        (
                            "This is a friendly reminder that the "
                            "abstract submission deadline is approaching."
                        ),
                        (
                            "We encourage you to complete and submit "
                            "your abstract before the deadline."
                        ),
                        (
                            f"Submission Deadline: "
                            f"{abstract_submission_deadline.strftime('%B %d, %Y')}"
                        ),
                        (
                            f"Conference Date: "
                            f"{conference.start_date.strftime('%B %d, %Y')}"
                        ),
                        (
                            f"Venue: {conference.venue_name}"
                        ),
                    ],
                    button_text="Submit Abstract",
                    button_url=abstract_url,
                    salutations=[
                        "Best regards,",
                        "USChE Organizing Committee",
                    ],
                    footer_text="© 2026 USChE - University of Dodoma",
                )

    except BadHeaderError as bhe:
        logger.error(
            f"Email sending failed due to BadHeaderError: {str(bhe)}",
            exc_info=True,
        )

    except Exception as e:
        logger.error(
            f"Email sending failed: {str(e)}",
            exc_info=True,
        )
        raise

