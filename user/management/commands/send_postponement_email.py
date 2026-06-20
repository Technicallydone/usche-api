from django.core.management.base import BaseCommand
from django.core.mail import send_mass_mail
from user.models import User
 
 
class Command(BaseCommand):
    help = 'Send postponement email to all users'
 
    def handle(self, *args, **kwargs):
        users = User.objects.filter(is_active=True).values_list('email', 'title', 'first_name')
 
        subject = 'USCHe 2026 - Conference Rescheduled to 29th - 31st July 2026'
        messages = []
 
        for email, title, first_name in users:
            title = title or ''
            name = first_name or ''
            salutation = f"{title} {name}".strip() if title or name else 'Participant'
 
            body = f"""Dear {salutation},
 
I hope you are doing well.
 
Due to unavoidable circumstances the 3rd UDOM Scientific Conference on Health (USCHe) has been rescheduled to 29th - 31st July 2026.
 
Please receive our sincere apologies for the inconvenience caused by this change of dates.
 
Kindly accept to reschedule, attend and be part of the conference on these new dates. We will communicate program details and logistics more concretely in the days to come and in good time to allow preparations.
 
Sincerely,
Secretariat - UDOM Scientific Conference on Health"""
 
            messages.append((subject, body, 'usche.info@gmail.com', [email]))
 
        total = len(messages)
        self.stdout.write(f'Sending emails to {total} users...')
 
        send_mass_mail(tuple(messages), fail_silently=False)
 
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {total} emails.'))