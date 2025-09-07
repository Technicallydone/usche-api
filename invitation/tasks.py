
import logging
from conference.models import Conference
from invitation.models import Invitation
from utils.send_email import send_invitation_email
from celery import shared_task


logger = logging.getLogger(__name__)

@shared_task()
def send_low_invitation_email():
    try:
        conference = Conference.get_latest_conference()
        
        if conference is None:
            return
        
        if conference.is_conference_outdated():
            return
        
        invitation = Invitation.get_conference_invitation(conference=conference)
        
        if invitation is None:
            return
        
        send_invitation_email(user=invitation.user, conference=invitation.conference)
        invitation.mark_invitation_sent()
        logger.info(f"Invitation sent to user: {invitation.user}")
        
    except Exception as e:
        logger.error(f"Error while sending an invitation email: {e}", exc_info=True)