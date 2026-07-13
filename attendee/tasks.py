import logging
from datetime import timedelta

from celery import Task, shared_task
from django.db import transaction
from django.utils import timezone

from attendee.models import Attendee
from conference.models import Conference
from user.models import User
from django.db.models import Q

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={'max_retries': 5}
)
def sync_recent_logged_in_users_as_attendees(self: Task):
    """
    Finds recently logged in users and automatically
    registers them as attendees for the active conference.
    """

    try:
        active_conference = (
            Conference.objects
            .filter(
                end_date__gte=timezone.now().date(),
            )
            .filter(
                Q(abstract_submission_open=True) |
                Q(attendee_registration_open=True)
            )
            .order_by("-listing_date")
            .first()
        )

        if active_conference is None:
            logger.info(
                "No active conference found for attendee sync."
            )
            return

        recent_login_threshold = timezone.now() - timedelta(hours=24)

        recent_users = User.objects.filter(
            is_active=True,
            last_login__gte=recent_login_threshold
        )

        created_count = 0
        skipped_count = 0

        for user in recent_users:
            attendee_exists = Attendee.objects.filter(
                participant=user,
                conference=active_conference
            ).exists()

            if attendee_exists:
                skipped_count += 1
                continue

            with transaction.atomic():
                Attendee.objects.create(
                    participant=user,
                    conference=active_conference
                )

            created_count += 1

            logger.info(
                f"Created attendee for user {user.email} "
                f"in conference "
                f"{active_conference.conference_name}"
            )

        logger.info(
            f"Attendee sync completed. "
            f"Created: {created_count}, "
            f"Skipped: {skipped_count}"
        )

    except Exception as e:
        logger.error(
            f"Failed to sync attendees automatically: {str(e)}",
            exc_info=True
        )

        raise self.retry(exc=e)