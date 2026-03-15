from datetime import timedelta
from typing import Dict
from celery import shared_task
from django.db import transaction
from django.core.mail import BadHeaderError
from conference.model import Conference
from invitation.models import Invitation
from settings.models import Settings
from usche_app import settings
from user.models import User
from utils.beem_sms import BeemSMSClient
from utils.send_email import  send_activation_email, send_reminder_email
import logging
from django.utils.timezone import now
from django.utils import timezone
from utils.access_token import generate_token
from utils.uniode_strip import strip_unicode



logger = logging.getLogger(__name__)

@shared_task()
def send_low_priority_email():
    try:
        with transaction.atomic():
            ten_minutes_ago = now() - timedelta(minutes=10)

            user = User.objects.filter(
                created_at__lte=ten_minutes_ago, 
                is_active=False, 
                has_sent_activation_email=False
            ).order_by('-created_at').first()

            if user:

                send_activation_email(user=user)
                
                user.has_sent_activation_email = True
                user.save(update_fields=['has_sent_activation_email'])
            
    except BadHeaderError as bhe:
        logger.error(f"Email sending failed due to BadHeaderError: {str(bhe)}", exc_info=True)

    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
        

@shared_task()
def send_high_priority_email():
    sms = BeemSMSClient()
    
    try:
        with transaction.atomic():

            user = User.objects.filter(is_active=False, resend_activation_email=True).order_by('-created_at').first()

            if user:
                # send_activation_email(user=user)
                user.resend_activation_email = False
                user.save(update_fields=['resend_activation_email'])
                token = generate_token(user=user)
                

                send_activation_email(user=user)
                
                try:
                    message = (
                        f"Dear {user.title} {user.last_name},\n\n"
                        "Your registration is successful. Please click the link below to activate your account:\n\n"
                        f"link: {settings.FRONTEND_BASE_URL}/activate/{token}"
                    )


                    sms_response = sms.send_sms(
                        message=strip_unicode(message),
                        recipients=[user.phone_number]
                    )

                    logger.info(f"SMS sent successfully: {sms_response}")
                except Exception as sms_error:
                    logger.error(f"SMS sending failed: {str(sms_error)}", exc_info=True)
            
    except BadHeaderError as bhe:
        logger.error(f"Email sending failed due to BadHeaderError: {str(bhe)}", exc_info=True)

    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
        

    
@shared_task
def send_deadline_reminder_high_priority_email():
    try:
        with transaction.atomic():
            conference = Conference.get_latest_conference()

            if conference.is_conference_outdated():
                return

            abstract_submission_deadline = conference.abstract_submission_deadline
            now = timezone.now()

            days_until_deadline = (abstract_submission_deadline.date() - now.date()).days

            if not 0 <= days_until_deadline <= 14:
                return

            users_to_remind = Invitation.objects.filter(
                conference=conference,
                user__abstracts__isnull=True
            ).values_list('user', flat=True).distinct()


            users_to_notify = User.objects.filter(user_id__in=users_to_remind).distinct()

            for user in users_to_notify:
                logger.info(f"Sending reminder email to: {user.email}")
                send_reminder_email(user, conference)

    except BadHeaderError as bhe:
        logger.error(f"Email sending failed due to BadHeaderError: {str(bhe)}", exc_info=True)

    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
        
        
@shared_task
def send_registration_payment_reminder_low_priority_email():
    try:
        sms = BeemSMSClient()

        with transaction.atomic():
            # Load required settings and latest conference info
            support = Settings.get_contact_support()
            contact_number = support.phone_support
            conference = Conference.get_latest_conference()
            conference_date = conference.start_date

            # URLs
            base_url = settings.FRONTEND_BASE_URL
            abstract_link_attendee = f"{base_url}/dashboard/abstract"
            abstract_link_other = f"{base_url}/panel/submit-abstract"
            payment_link = f"{base_url}/dashboard/conference/join"

            # Get users who have neither payment nor abstract
            users = User.users_without_abstract_and_payment(conference=conference)

            for user in users:
                message = (
                    f"Dear {user.title} {user.last_name},\n\n"
                    f"Reminder: USCHe 2025 starts on {conference_date}. "
                    f"Pay and upload slip at: {payment_link}\n\n"
                    f"Questions? Call {contact_number}."
                )


                # Send email
                # send_registration_payment_reminder_email(user, conference)

                # Send SMS
                try:
                    response = sms.send_sms(
                        message=strip_unicode(message).strip(),
                        recipients=[user.phone_number]
                    )
                    logger.info(f"SMS sent to {user.phone_number}: {response}")
                except Exception as sms_error:
                    logger.error(f"Failed to send SMS to {user.phone_number}: {str(sms_error)}", exc_info=True)

    except BadHeaderError as bhe:
        logger.error("Email failed due to BadHeaderError", exc_info=True)
    except Exception as e:
        logger.error("Reminder task failed", exc_info=True)
