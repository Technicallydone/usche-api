from datetime import timedelta

from celery import shared_task
from django.core.mail import BadHeaderError
from django.db import transaction
from django.utils import timezone

from conference.model import Conference
from invitation.models import Invitation
from services.email.tasks import send_email_task
from usche_app import settings
from user.models import User

import logging


logger = logging.getLogger(__name__)


@shared_task
def send_deadline_reminder_high_priority_email():
    try:
        with transaction.atomic():

            current_time = timezone.now()
            reminder_limit = current_time + timedelta(days=14)

            conferences = Conference.objects.filter(
                end_date__gte=current_time.date()
            )

            if not conferences.exists():
                logger.info("No active conferences found.")
                return

            for conference in conferences:

                # ======================================================
                # ABSTRACT SUBMISSION REMINDERS
                # ======================================================
                if (
                    conference.abstract_submission_open
                    and current_time <= conference.abstract_submission_deadline
                    <= reminder_limit
                ):

                    users_without_abstract = (
                        Invitation.objects
                        .filter(
                            conference=conference,
                            user__abstracts__isnull=True,
                        )
                        .values_list("user_id", flat=True)
                        .distinct()
                    )

                    abstract_users = (
                        User.objects
                        .filter(user_id__in=users_without_abstract)
                        .distinct()
                    )

                    abstract_url = (
                        f"{settings.FRONTEND_BASE_URL}/dashboard/abstract"
                    )

                    for user in abstract_users:
                        logger.info(
                            "Sending abstract reminder to %s for %s",
                            user.email,
                            conference.conference_name,
                        )

                        send_email_task.delay(
                            subject=(
                                f"Abstract Submission Reminder - "
                                f"{conference.conference_name}"
                            ),
                            to=user.email,
                            greeting=(
                                f"Dear {user.title or ''} "
                                f"{user.last_name or ''},"
                            ).strip(),
                            lines=[
                                (
                                    "This is a friendly reminder that "
                                    "abstract submission is still open."
                                ),
                                (
                                    f"Submission Deadline: "
                                    f"{conference.abstract_submission_deadline.strftime('%B %d, %Y %I:%M %p')}"
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


                # ======================================================
                # ATTENDEE REGISTRATION REMINDERS
                # ======================================================
                if (
                    conference.attendee_registration_open
                    and current_time <= conference.attendee_registration_deadline
                    <= reminder_limit
                ):

                    users_without_registration = (
                        Invitation.objects
                        .filter(
                            conference=conference,
                            user__attendees__isnull=True,
                        )
                        .values_list("user_id", flat=True)
                        .distinct()
                    )

                    attendee_users = (
                        User.objects
                        .filter(user_id__in=users_without_registration)
                        .distinct()
                    )

                    registration_url = (
                        f"{settings.FRONTEND_BASE_URL}/dashboard/register"
                    )

                    for user in attendee_users:
                        logger.info(
                            "Sending attendee registration reminder to %s for %s",
                            user.email,
                            conference.conference_name,
                        )

                        send_email_task.delay(
                            subject=(
                                f"Conference Registration Reminder - "
                                f"{conference.conference_name}"
                            ),
                            to=user.email,
                            greeting=(
                                f"Dear {user.title or ''} "
                                f"{user.last_name or ''},"
                            ).strip(),
                            lines=[
                                (
                                    "This is a friendly reminder that "
                                    "conference registration is still open."
                                ),
                                (
                                    f"Registration Deadline: "
                                    f"{conference.attendee_registration_deadline.strftime('%B %d, %Y %I:%M %p')}"
                                ),
                                (
                                    f"Conference Date: "
                                    f"{conference.start_date.strftime('%B %d, %Y')}"
                                ),
                                (
                                    f"Venue: {conference.venue_name}"
                                ),
                            ],
                            button_text="Register Now",
                            button_url=registration_url,
                            salutations=[
                                "Best regards,",
                                "USChE Organizing Committee",
                            ],
                            footer_text="© 2026 USChE - University of Dodoma",
                        )

    except BadHeaderError as bhe:
        logger.error(
            "Email sending failed due to BadHeaderError: %s",
            str(bhe),
            exc_info=True,
        )

    except Exception as e:
        logger.error(
            "Email sending failed: %s",
            str(e),
            exc_info=True,
        )
        raise