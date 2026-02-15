import logging
from conference.models import Conference
from .models import Invitation
from services.email.tasks import send_email_task
from celery import shared_task

from utils.document_generator import generate_invitation_pdf

logger = logging.getLogger(__name__)

@shared_task()
def send_low_invitation_email():
    try:
        # Get latest conference
        conference = Conference.get_latest_conference()
        if conference is None or conference.is_conference_outdated():
            return

        # Get invitation for the conference
        invitation = Invitation.get_conference_invitation(conference=conference)
        if invitation is None:
            return

        # Generate PDF for the invitation
        pdf = generate_invitation_pdf(user=invitation.user, conference=conference)
        if not pdf:
            raise Exception("Failed to generate PDF for invitation")

        # Prepare attachments
        attachments = [
            {
                "filename": "Invitation_Letter.pdf",
                "content": pdf.getvalue(),  # bytes
                "mime_type": "application/pdf",
            }
        ]

        # Queue email via send_email_task
        send_email_task.delay(
            subject=f"USChE-{conference.start_date.year} Participant Invitation Letter",
            to=invitation.user.email,
            greeting=f"Dear {invitation.user.title} {invitation.user.last_name},",
            lines=[
                "We are pleased to invite you to the upcoming event.",
                f"Event Date: {conference.start_date}",
                f"Venue: {conference.venue_name}"
            ],
            salutations=["Best regards,", "Event Organizing Team"],
            footer_text="© 2026 USChE - University of Dodoma",
            attachments=attachments
        )

        # Mark invitation as sent
        invitation.mark_invitation_sent()
        logger.info(f"Invitation email queued for {invitation.user.email}")

    except Exception as e:
        logger.error(f"Error while sending an invitation email: {e}", exc_info=True)
        raise
