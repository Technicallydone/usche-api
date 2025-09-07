import base64
import logging
import os
from django.core.mail import EmailMessage
import requests

from abstracts.model.abstract import Abstract
from attendee.models import Attendee
from certificate.models import Certificate
from conference.models import BankAccount, Conference
from usche_app import settings
from user.models import User
from utils.crypto_utils import encrypt_data
from utils.document_generator import generate_invitation_pdf, generate_certificate_pdf
from utils.qr_code_generator import generate_qr_code
from utils.access_token import generate_token
from django.template.loader import render_to_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_certificate_email(cert: Certificate):
    """
    Sends a certificate email with a PDF attachment using the secure mail service.
    """
    try:
        # Generate certificate PDF
        pdf_bytes = generate_certificate_pdf(cert.user, cert.conference)

        if not pdf_bytes:
            logger.error(f"Failed to generate PDF for {cert.user.email} - {cert.conference.conference_name}")
            return

        # Create subject and render HTML
        subject = "Your USCHE Participation Certificate"
        html_content = render_to_string("usche_certificate_email_template.html", {
            "name": cert.user.first_name,
            "logo_url": f"{settings.APP_BASE}/media/usche/usche_logo.png"
        })

        # Encrypt message and subject
        encrypted_message, iv_message, message_key = encrypt_data(html_content)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        # Base64 encode PDF
        encoded_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        encrypted_pdf, iv_pdf, pdf_key = encrypt_data(encoded_pdf)

        # Prepare payload
        payload = {
            "priority": 2,
            "rq_id": str(cert.user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": cert.user.email,
            "attachments": [
                {
                    "data": encrypted_pdf,
                    "filename": "USCHE_Certificate.pdf",
                    "mime_type": "application/pdf",
                    "iv": base64.b64encode(iv_pdf).decode('utf-8'),
                    "key": base64.b64encode(pdf_key).decode('utf-8')
                }
            ]
        }

        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info(f"Certificate email sent to {cert.user.email}")
        else:
            logger.error(f"Failed to send certificate email to {cert.user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Exception sending certificate email to {cert.user.email}: {e}", exc_info=True)
        raise


def send_feedback_email(user: User):
    """
    Sends a feedback invitation email to the user using the secure mail service.
    """
    try:
        subject = "We Value Your Feedback - USCHE Conference"

        html_content = render_to_string("usche_feedback_email_template.html", {
            "name": user.first_name,
            "logo_url": f"{settings.APP_BASE}/media/usche/usche_logo.png",
        })

        encrypted_message, iv_message, message_key = encrypt_data(html_content)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        payload = {
            "priority": 2,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
            "attachments": []  
        }

        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info(f"Feedback email sent to {user.email}")
        else:
            logger.error(f"Failed to send feedback email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Exception sending feedback email to {user.email}: {e}", exc_info=True)
        raise
    

def send_payment_approval_email(user: User):
    """
    Sends a confirmation email to the user after their payment is approved using the secure mail service.
    """
    try:
        subject = "Your Payment Has Been Approved!"

        html_content = render_to_string("payment_approval_email_template.html", {
            "title": user.title,
            "last_name": user.last_name,
            "dashboard_url": f"{settings.FRONTEND_BASE_URL}/auth",
        })

        encrypted_message, iv_message, message_key = encrypt_data(html_content)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        payload = {
            "priority": 2,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
            "attachments": []  
        }

        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info(f"Payment approval email sent to {user.email}")
        else:
            logger.error(f"Failed to send payment approval email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Exception sending payment approval email to {user.email}: {e}", exc_info=True)
        raise


# def send_payment_approval_email(user: User):
#     """
#     Sends a confirmation email to the user after their payment is approved.
#     """
#     try:
#         subject = "Your Payment Has Been Approved!"

#         # Render the message using a template (or create the message directly)
#         html_content = render_to_string("payment_approval_email_template.html", {
#             "title": user.title,
#             "last_name": user.last_name,
#             "dashboard_url": f"{settings.FRONTEND_BASE_URL}/auth",
#         })

#         email = EmailMessage(
#             subject=subject,
#             body=html_content,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email],
#             reply_to=[settings.DEFAULT_FROM_EMAIL],
#         )
#         email.content_subtype = "html"
#         email.send(fail_silently=False)

#         logger.info(f"Payment approval email sent to {user.email}")

#     except Exception as e:
#         logger.error(f"Failed to send payment approval email to {user.email}: {e}", exc_info=True)
#         raise

# TO DUMA
def send_registration_payment_reminder_email(user: User, conference: Conference):

    try:
        subject = "USCHe-2025 Registration Payment Reminder"

        message = render_to_string("registration_payment_reminder_template.html", {
            "start_date": conference.start_date,
            "deadline": conference.abstract_submission_deadline,
            "title": user.title,
            "last_name": user.last_name,
            "venue": conference.venue_name,
        })

        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        file_path = os.path.join(settings.MEDIA_ROOT, "usche", "upr.pdf")
        
        with open(file_path, "rb") as file:
            encoded_image = base64.b64encode(file.read()).decode('utf-8')

        encrypted_image, iv_image, image_key = encrypt_data(encoded_image)

        # Build the email payload
        payload = {
            "priority": 2,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
            "attachments": [
                {
                    "data": encrypted_image,
                    "filename": "Payment reminder for conference registrants.pdf",
                    "mime_type": "application/pdf",
                    "iv": base64.b64encode(iv_image).decode('utf-8'),
                    "key": base64.b64encode(image_key).decode('utf-8')
                }
            ]
        }

        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info(f"Reminder email sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Failed to send reminder email to {user.email}: {e}", exc_info=True)
        raise

# def send_registration_payment_reminder_email(user: User, conference: Conference):
#     """
#     Sends a registration payment reminder email with an attached PDF.
#     """
#     try:
#         subject = "USCHe-2025 Registration Payment Reminder"

#         # Render the HTML content for the email
#         html_content = render_to_string("registration_payment_reminder_template.html", {
#             "start_date": conference.start_date,
#             "deadline": conference.abstract_submission_deadline,
#             "title": user.title,
#             "last_name": user.last_name,
#             "venue": conference.venue_name,
#         })

#         # Create email object
#         email = EmailMessage(
#             subject=subject,
#             body=html_content,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email],
#             reply_to=[settings.DEFAULT_FROM_EMAIL],
#         )
#         email.content_subtype = "html"  # Set content to HTML

#         # Attach PDF
#         file_path = os.path.join(settings.MEDIA_ROOT, "usche", "upr.pdf")
#         if os.path.exists(file_path):
#             with open(file_path, 'rb') as pdf_file:
#                 email.attach(
#                     filename="Payment reminder for conference registrants.pdf",
#                     content=pdf_file.read(),
#                     mimetype="application/pdf"
#                 )
#         else:
#             logger.warning(f"Attachment not found at {file_path}, email sent without it.")

#         # Send email
#         email.send(fail_silently=False)
#         logger.info(f"Reminder email sent successfully to {user.email}")

#     except Exception as e:
#         logger.error(f"Failed to send reminder email to {user.email}: {e}", exc_info=True)
#         raise

def send_reminder_email(user: User, conference: Conference):
  

    try:
        subject = "USCHe-2025 Abstract Submission Deadline Approaching"

        # Render the HTML email template
        message = render_to_string("reminder_email_template.html", {
            "start_date": conference.start_date,
            "deadline": conference.abstract_submission_deadline,
            "title": user.title,
            "last_name": user.last_name,
            "venue": conference.venue_name,
        })

        # Encrypt the subject and message
        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        # Load the image from the media directory
        image_path = os.path.join(settings.MEDIA_ROOT, "usche", "extension.jpeg")
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        encrypted_image, iv_image, image_key = encrypt_data(encoded_image)

        # Build the email payload
        payload = {
            "priority": 2,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
            "attachments": [
                {
                    "data": encrypted_image,
                    "filename": "submission_deadline_reminder.jpeg",
                    "mime_type": "image/jpeg",
                    "iv": base64.b64encode(iv_image).decode('utf-8'),
                    "key": base64.b64encode(image_key).decode('utf-8')
                }
            ]
        }

        # Headers
        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        # Send the request
        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info(f"Reminder email sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Failed to send reminder email to {user.email}: {e}", exc_info=True)
        raise


def send_reset_password_email(user: User):
    """
    Sends an account activation email to the user with a secure token.
    """
    try:
        # Generate secure token for the activation link
        token = generate_token(user=user)
        if not token:
            raise Exception("Failed to generate token")

        # Prepare the activation URL
        activation_url = f"{settings.FRONTEND_BASE_URL}/auth/reset-password/{token}"
        subject = "Password Reset"
        
        # Prepare the HTML message
        message = render_to_string("reset_password_email_template.html", {
            "activation_url": activation_url,
            "title": user.title,
            "last_name": user.last_name,
        })

        # Encrypt the message and subject
        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        # Prepare the payload for the mail service
        payload = {
            "priority": 1,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
        }

        # Send the email by making a POST request to the mail service
        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        # Check the response from the email service
        if response.status_code == 200:
            logger.info(f"reset password email sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Failed to send reset password email to {user.email}: {e}", exc_info=True)
        raise



def send_invitation_email(user: User, conference: Conference):
    """
    Sends an invitation email with a PDF attachment by making a POST request
    to the mail service at http://127.0.0.1:8000/mail/send/.
    """

    try:
        # Generate PDF for the invitation
        pdf = generate_invitation_pdf(user=user, conference=conference)
        if not pdf:
            raise Exception("Failed to generate PDF")

        # Prepare the subject and message body
        subject = "USCHe-2025 Participant Invitation Letter"
        message = render_to_string("email_template.html", {
            "start_date": conference.start_date,
            "title": user.title,
            "venue": conference.venue_name,
            "last_name": user.last_name,
        })

        # Encrypt the message
        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        # Encrypt the PDF attachment
        encoded_pdf = base64.b64encode(pdf.getvalue()).decode('utf-8')
        encrypted_pdf, iv_pdf, pdf_key = encrypt_data(encoded_pdf)

        # Prepare the payload for the mail service
        payload = {
            "priority": 2,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
            "attachments": [
                {
                    "data": encrypted_pdf,
                    "filename": "Invitation_Letter.pdf",
                    "mime_type": "application/pdf",
                    "iv": base64.b64encode(iv_pdf).decode('utf-8'),
                    "key": base64.b64encode(pdf_key).decode('utf-8')
                }
            ]
        }

        # Send the email by making a POST request to the mail service
        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        # Check the response from the email service
        if response.status_code == 200:
            logger.info(f"Invitation email sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Failed to send invitation email to {user.email}: {e}", exc_info=True)
        raise



# TO DUMA
def send_payment_rejection_email(user: User, comment: str):
    """
    Sends a rejection email to the user with the reason for the payment rejection.
    
    Args:
        user (User): The user receiving the rejection email.
        comment (str): The reason for the payment rejection to be included in the email message.
    """
    try:
        # Prepare the email subject and message content
        subject = "Payment Rejection Notification"
        
        # Render the email message from a template
        message = render_to_string("payment_rejection_email_template.html", {
            "title": user.title,
            "last_name": user.last_name,
            "comment": comment
        })

        # Encrypt the subject and message content
        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        # Prepare the payload for the mail service
        payload = {
            "priority": 1,
            "rq_id": str(user.id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
        }

        # Set headers for the mail service
        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        # Send the email by making a POST request to the mail service
        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        # Check the response from the mail service
        if response.status_code == 200:
            logger.info(f"Payment rejection email sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Unexpected error in send_payment_rejection_email for {user.email}: {e}", exc_info=True)
        raise

# def send_payment_rejection_email(user: User, comment):
#     """
#     Sends a payment rejection email to the user with the given comment.
    
#     Args:
#         user (User): The user receiving the rejection email.
#         comment (str): The reason for the payment rejection.
#     """
#     try:
#         subject = "Payment Rejection Notification"

#         html_content = render_to_string("payment_rejection_email_template.html", {
#             "title": user.title,
#             "last_name": user.last_name,
#             "comment": comment
#         })

#         email = EmailMessage(
#             subject=subject,
#             body=html_content,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email],
#             reply_to=[settings.DEFAULT_FROM_EMAIL]
#         )
#         email.content_subtype = "html" 
#         email.send(fail_silently=False)

#         logger.info(f"Payment rejection email sent successfully to {user.email}")

#     except Exception as e:
#         logger.error(f"Failed to send payment rejection email to {user.email}: {e}", exc_info=True)
#         raise


# TO DUMA
def send_rejection_email(user: User, comment: str):
    """
    Sends a rejection email to the user with a reason for abstract rejection.
    
    Args:
        user (User): The user receiving the rejection email.
        comment (str): The reason for the rejection to be included in the email message.
    """
    try:
        # Prepare the email subject and message content
        subject = "Abstract Rejection Notification"
        
        # Render the email message from a template
        message = render_to_string("rejection_email_template.html", {
            "title": user.title,
            "last_name": user.last_name,
            "comment": comment
        })

        # Encrypt the subject and message
        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        # Prepare the payload for the mail service
        payload = {
            "priority": 1,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
        }

        # Set headers for the mail service
        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        # Send the email by making a POST request to the mail service
        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        # Check the response from the mail service
        if response.status_code == 200:
            logger.info(f"Rejection email sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Unexpected error in send_rejection_email for {user.email}: {e}", exc_info=True)
        raise

# def send_rejection_email(user: User, comment):
#     """
#     Sends a rejection email to the user with a reason for abstract rejection.

#     Args:
#         user (User): The user receiving the rejection email.
#         comment (str): The reason for the rejection to be included in the email message.
#     """
#     try:
#         subject = "Abstract Rejection Notification"

#         html_content = render_to_string("rejection_email_template.html", {
#             "title": user.title,
#             "last_name": user.last_name,
#             "comment": comment,
#         })

#         email = EmailMessage(
#             subject=subject,
#             body=html_content,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email],
#             reply_to=[settings.DEFAULT_FROM_EMAIL],
#         )
#         email.content_subtype = "html" 

#         email.send(fail_silently=False)
#         logger.info(f"Rejection email sent successfully to {user.email}")

#     except Exception as e:
#         logger.error(f"Failed to send rejection email to {user.email}: {e}", exc_info=True)
#         raise



def send_qr_code_email(attendee: Attendee):
    """
    Sends an email with a QR code as an attachment via an external mail service.
    
    Args:
        attendee: The attendee object containing email details.
    """
    try:
        # Generate QR code data and image
        qr_data = f"ID:{attendee.attendee_id},U:sche"
        qr_image = generate_qr_code(qr_data)  # This function generates the QR code image
        
        # Render the email message from a template
        subject = "Your Authentication QR Code"
        message = render_to_string("qr_code_email_template.html", {
            "title": attendee.participant.title,
            "first_name": attendee.participant.first_name,
        })

        # Encrypt the message and subject
        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)
        
        qr_encoded = base64.b64encode(qr_image.read()).decode('utf-8')
        encrypted_qr, iv_qr, qr_key = encrypt_data(qr_encoded)

        # Prepare the payload for the mail service
        payload = {
            "priority": 1,
            "rq_id": str(attendee.attendee_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": attendee.participant.email,
            "attachments": [{
                "filename": "qr_code.png",
                "content": encrypted_qr,
                "type": "image/png",
                "iv": base64.b64encode(iv_qr).decode('utf-8'),
                "key": base64.b64encode(qr_key).decode('utf-8')
            }]
        }

        # Set headers for the mail service
        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        # Send the email by making a POST request to the mail service
        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        # Check the response from the mail service
        if response.status_code == 200:
            logger.info(f"QR code email sent successfully to {attendee.participant.email}")
        else:
            logger.error(f"Failed to send email to {attendee.participant.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Unexpected error in send_qr_code_email for {attendee.participant.email}: {e}", exc_info=True)
        raise


# def send_qr_code_email(attendee: Attendee):
#     """
#     Sends an email with a QR code as an attachment.
    
#     Args:
#         user: The user object containing email details.
#     """
#     try:
#         qr_data = f"ID:{attendee.attendee_id},U:sche"
#         qr_image = generate_qr_code(qr_data)

#         subject = "Your Authentication QR Code"
#         message = f"""
#         <html>
#         <head>
#             <style>
#                 body {{ font-family: 'Arial', sans-serif; }}
#                 .container {{ padding: 20px; }}
#                 .footer {{ margin-top: 20px; font-size: 14px; color: #666; }}
#             </style>
#         </head>
#         <body>
#             <div class="container">
#                 <h2>Hello {attendee.participant.title} {attendee.participant.first_name},</h2>
#                 <p>Please find your QR code attached below. Scan this QR code to authenticate yourself.</p>
#                 <p class="footer">Best Regards,<br>USCHe</p>
#             </div>
#         </body>
#         </html>
#         """

#         email = EmailMessage(
#             subject,
#             message,
#             settings.DEFAULT_FROM_EMAIL,
#             [attendee.participant.email]
#         )
#         email.content_subtype = "html"
#         email.attach("qr_code.png", qr_image.read(), "image/png") 

#         email.send()
#         logger.info(f"QR code email sent successfully to {attendee.participant.email}")

#     except Exception as e:
#         logger.error(f"Failed to send QR code email to {attendee.participant.email}: {e}")
#         raise

# TARGET TO DUMA
def send_activation_email(user: User):
    """
    Sends an account activation email to the user with a secure token.
    """
    try:
        # Generate secure token for the activation link
        token = generate_token(user=user)
        if not token:
            raise Exception("Failed to generate token")

        # Prepare the activation URL
        activation_url = f"{settings.FRONTEND_BASE_URL}/activate/{token}"
        subject = "Activate Your Account"
        
        # Prepare the HTML message
        message = render_to_string("activation_email_template.html", {
            "activation_url": activation_url,
            "title": user.title,
            "last_name": user.last_name,
        })

        # Encrypt the message and subject
        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        # Prepare the payload for the mail service
        payload = {
            "priority": 1,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
        }

        # Send the email by making a POST request to the mail service
        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        # Check the response from the email service
        if response.status_code == 200:
            logger.info(f"Activation email sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Failed to send activation email to {user.email}: {e}", exc_info=True)
        raise


# def send_activation_email(user: User):
#     """
#     Sends an account activation email to the user using Django's EmailMessage (SMTP/SES).
#     """
#     try:
#         try:
#             token = generate_token(user=user)
#         except Exception as e:
#             logger.error(f"Token generation failed for user {user.email}: {e}")
#             raise

#         activation_url = f"{settings.FRONTEND_BASE_URL}/activate/{token}"
#         subject = "Activate Your Account"

#         html_content = f"""
#         <!DOCTYPE html>
#         <html lang="en">
#         <head>
#             <meta charset="UTF-8">
#             <meta name="viewport" content="width=device-width, initial-scale=1.0">
#             <title>Account Activation</title>
#             <style>
#                 body {{
#                     font-family: 'Poppins', sans-serif;
#                     background-color: #FFF9E6;
#                     margin: 0;
#                     padding: 0;
#                     color: #3C4B64;
#                 }}
#                 .container {{
#                     max-width: 600px;
#                     margin: 0 auto;
#                     padding: 20px;
#                     background-color: #ffffff;
#                     border-radius: 8px;
#                     box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#                 }}
#                 .header {{
#                     font-size: 24px;
#                     font-weight: bold;
#                     color: #0864cc;
#                 }}
#                 .title {{
#                     font-size: 20px;
#                     color: #F4A900;
#                 }}
#                 .message {{
#                     font-size: 16px;
#                     margin-top: 15px;
#                 }}
#                 .cta-button {{
#                     display: inline-block;
#                     padding: 10px 20px;
#                     background-color: #0864cc;
#                     color: white;
#                     text-decoration: none;
#                     border-radius: 4px;
#                     margin-top: 20px;
#                     font-size: 16px;
#                 }}
#                 .footer {{
#                     font-size: 14px;
#                     color: #F4A900;
#                     margin-top: 30px;
#                 }}
#             </style>
#         </head>
#         <body>
#             <div class="container">
#                 <div class="header">
#                     Dear {user.title} {user.last_name},
#                 </div>
#                 <div class="message">
#                     <p>Please activate your account by clicking the link below:</p>
#                     <a href="{activation_url}" class="cta-button">Activate Account</a>
#                     <p>This link will expire in 1 hour. If you did not request this, please ignore this email.</p>
#                 </div>
#                 <div class="footer">
#                     <p>Regards,</p>
#                     <p>USCHe</p>
#                 </div>
#             </div>
#         </body>
#         </html>
#         """

#         email = EmailMessage(
#             subject=subject,
#             body=html_content,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email],
#             reply_to=[settings.DEFAULT_FROM_EMAIL],
#         )
#         email.content_subtype = "html"

#         email.send(fail_silently=False)
#         logger.info(f"Activation email sent successfully to {user.email}")

#     except Exception as e:
#         logger.error(f"Failed to send activation email to {user.email}: {e}", exc_info=True)
#         raise

# TO DUMA

def send_payment_email(user: User, abstract: Abstract, bank_account: BankAccount):
    """
    Sends a payment request email to the user with bank account details for payment.
    """
    try:
        payment_url = f"{settings.FRONTEND_BASE_URL}/dashboard/abstract/my-abstract"
        subject = "Abstract Approval"
        
        message = render_to_string("payment_email_template.html", {
            "title": user.title,
            "last_name": user.last_name,
            "abstract": str(abstract.title),
            "bank_name": bank_account.bank_name,
            "account_number": bank_account.account_number,
            "account_name": bank_account.account_name,
            "swift_code": bank_account.swift_code,
            "payment_url": payment_url
        })

        # Encrypt the message
        encrypted_message, iv_message, message_key = encrypt_data(message)
        enc_subject, iv_subject, subject_key = encrypt_data(subject)

        # Prepare the payload for the mail service
        payload = {
            "priority": 1,
            "rq_id": str(user.user_id),
            "encrypted_text": encrypted_message,
            "subject": enc_subject,
            "sub_iv": base64.b64encode(iv_subject).decode('utf-8'),
            "sub_key": base64.b64encode(subject_key).decode('utf-8'),
            "iv": base64.b64encode(iv_message).decode('utf-8'),
            "key": base64.b64encode(message_key).decode('utf-8'),
            "to": user.email,
            "attachments": []
        }

        # Send the email by making a POST request to the mail service
        headers = {
            'Authorization': f'Bearer {settings.MAIL_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.MAIL_ENDPOINT, json=payload, headers=headers)

        # Check the response from the email service
        if response.status_code == 200:
            logger.info(f"Payment request email sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send email to {user.email}: {response.text}")
            raise Exception(f"Mail Service Error: {response.text}")

    except Exception as e:
        logger.error(f"Unexpected error in send_payment_email for {user.email}: {e}", exc_info=True)
        raise

# def send_payment_email(user: User, abstract: Abstract, bank_account: BankAccount):
#     """
#     Sends a payment request email to the user with bank account details for payment.
#     """
#     try:
#         payment_url = f"{settings.FRONTEND_BASE_URL}/dashboard/abstract/my-abstract"
#         subject = "Payment Request for Your Abstract Submission"

#         # Render HTML content from a template
#         html_content = render_to_string("payment_email_template.html", {
#             "title": user.title,
#             "last_name": user.last_name,
#             "abstract": str(abstract.title),
#             "bank_name": bank_account.bank_name,
#             "account_number": bank_account.account_number,
#             "account_name": bank_account.account_name,
#             "swift_code": bank_account.swift_code,
#             "payment_url": payment_url
#         })

#         email = EmailMessage(
#             subject=subject,
#             body=html_content,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email],
#             reply_to=[settings.DEFAULT_FROM_EMAIL],
#         )
#         email.content_subtype = "html" 

#         # Send email
#         email.send(fail_silently=False)
#         logger.info(f"Payment request email sent successfully to {user.email}")

#     except Exception as e:
#         logger.error(f"Failed to send payment email to {user.email}: {e}", exc_info=True)
#         raise
