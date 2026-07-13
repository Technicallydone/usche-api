import logging
from django.utils import timezone
from celery import shared_task

from django.db.models import Max

from .models import Invitation
from attendee.models import Attendee
from services.email.tasks import send_email_task
from utils.document_generator import generate_invitation_pdf

logger = logging.getLogger(__name__)


def get_today_start():
    now = timezone.now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_pending_invitations_email(self, daily_limit: int = 200):
    try:
        today_start = get_today_start()

        # -----------------------------------
        # GET LAST COUNT FOR TODAY
        # -----------------------------------
        last_sent = (
            Invitation.objects
            .filter(invitation_sent=True, sent_at__gte=today_start)
            .aggregate(max_count=Max("daily_sent_count"))
        )["max_count"] or 0

        remaining_quota = daily_limit - last_sent

        if remaining_quota <= 0:
            logger.info("Daily invitation limit reached.")
            return

        invitations = (
            Invitation.objects.select_related("user", "conference")
            .filter(invitation_sent=False)
            .order_by("invited_on")[:remaining_quota]
        )

        if not invitations:
            logger.info("No pending invitations found.")
            return

        sent_count = last_sent

        for invitation in invitations:
            try:
                conference = invitation.conference
                user = invitation.user

                if conference.is_conference_outdated():
                    continue

                pdf = generate_invitation_pdf(
                    user=user,
                    conference=conference
                )

                if not pdf:
                    logger.warning(f"PDF generation failed for {user.email}")
                    continue

                attachments = [
                    {
                        "filename": "Invitation_Letter.pdf",
                        "content": pdf.getvalue(),
                        "mime_type": "application/pdf",
                    }
                ]

                send_email_task.delay(
                    subject=f"USCHe-{conference.start_date.year} Official Invitation",
                    to=user.email,
                    greeting=f"Dear {user.title or ''} {user.last_name},",
                    lines=[
                        "We are pleased to formally invite you to the USChE Conference.",
                        f"Conference Date: {conference.start_date}",
                        f"Venue: {conference.venue_name}",
                        "Please find your official invitation letter attached."
                    ],
                    salutations=[
                        "Best regards,",
                        "Conference Organizing Committee"
                    ],
                    footer_text="© 2026 USChE - University of Dodoma",
                    attachments=attachments
                )

                # -----------------------------------
                # INCREMENT DAILY COUNTER
                # -----------------------------------
                sent_count += 1

                # -----------------------------------
                # MARK INVITATION SENT + STORE COUNT
                # -----------------------------------
                invitation.daily_sent_count = sent_count
                invitation.mark_invitation_sent()

                # overwrite sent_at already handled in method
                invitation.save(update_fields=["daily_sent_count"])

                # -----------------------------------
                # MARK ATTENDEE AS INVITED
                # -----------------------------------
                Attendee.objects.filter(
                    conference=conference,
                    participant=user
                ).update(invitation_sent=True)

                logger.info(
                    f"[{sent_count}/{daily_limit}] Sent to {user.email}"
                )

                # stop exactly at limit
                if sent_count >= daily_limit:
                    logger.info("Reached daily limit (50). Stopping task.")
                    break

            except Exception as e:
                logger.error(
                    f"Failed processing invitation {invitation.invitation_id}: {e}",
                    exc_info=True
                )
                continue

        logger.info(
            f"Batch completed. Final sent count: {sent_count}"
        )

    except Exception as exc:
        logger.error("Invitation task failed", exc_info=True)
        raise self.retry(exc=exc)