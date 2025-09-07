from typing import Dict
from celery import shared_task
from django.db import transaction
from django.core.mail import BadHeaderError
from abstracts.enums.abstract_status import AbstractStatus
from abstracts.model.abstract import Abstract
from conference.model.bank_account import BankAccount
from usche_app import settings
from user.enums.role import ROLE
from utils.beem_sms import BeemSMSClient
from utils.send_email import send_payment_email
import logging
from django.utils import timezone

from utils.uniode_strip import strip_unicode



logger = logging.getLogger(__name__)

# @shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 5})
# def process_require_payment(self, validated_data: Dict):
#     try:
#         with transaction.atomic():
#             abstract = Abstract.mark_as_require_payment(validated_data.get("abstract_id"))
#             conference = abstract.sub_theme.theme.conference
#             account = BankAccount.objects.filter(conference=conference).first()
                
#             send_payment_email(user=abstract.user, abstract=abstract, bank_account=account)
#             abstract.payment_email_sent()


#     except BadHeaderError as bhe:
#         logger.error(f"Email bad header error: {str(bhe)}", exc_info=True)
#         raise self.retry(exc=e)

#     except Exception as e:
#         logger.error(f"Email sending failed: {str(e)}", exc_info=True)
#         raise self.retry(exc=e)
    
    
@shared_task()
def process_require_payment():
    sms = BeemSMSClient()
    try:
        with transaction.atomic():
            abstract = Abstract.objects.filter(
                status=AbstractStatus.REQUIRE_PAYMENT.value,
                require_payment_email_sent=False,
            ).first()

            if not abstract:
                return

            conference = abstract.sub_theme.theme.conference
            account = BankAccount.objects.filter(conference=conference).first()

            send_payment_email(user=abstract.user, abstract=abstract, bank_account=account)
            abstract.payment_email_sent()
            
            abstract_link = (
                f"{settings.FRONTEND_BASE_URL}/dashboard/abstract/my-abstract"
                if abstract.user.role == ROLE.ATTENDEE.value
                else f"{settings.FRONTEND_BASE_URL}/panel/my-abstract"
            )

            try:
                message = (
                    f"Dear {abstract.user.title} {abstract.user.last_name},\n\n"
                    "Congratulations! Your abstract has been approved.\n\n"
                    f"{abstract_link}\n\n"
                    "Thank you for your participation."
                )

                sms_response = sms.send_sms(
                    message=strip_unicode(message),
                    recipients=[abstract.user.phone_number]
                )

                logger.info(f"SMS sent successfully: {sms_response}")

            except Exception as sms_error:
                logger.error(f"SMS sending failed: {str(sms_error)}", exc_info=True)


    except BadHeaderError as bhe:
        logger.error(f"Email bad header error: {str(bhe)}", exc_info=True)

    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
