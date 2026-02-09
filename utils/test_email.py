# views.py or any Python file

from django.core.mail import send_mail
from django.conf import settings

def send_simple_email():
    subject = 'Test Email'
    message = 'This is a test email from Django.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ['ramadhani.mbaga@udom.ac.tz']
    
    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=False,
    )


# Call the function
if __name__ == '__main__':
    send_simple_email()