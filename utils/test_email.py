# utils/test_email.py

from django.core.mail import send_mail, EmailMessage

from usche_app import settings

send_mail(
    subject='Test from SES',
    message='It worked!',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['mcharoprofg23@gmail.com'],
    fail_silently=False,
)
