# utils/test_email.py

from services.email.tasks import send_email_task

def send_test_email():
    subject = "Test Email from USChE"
    recipient = "godfrey.steven@codeblock.co.tz"
    greeting = "Hello Godfrey,"
    lines = [
        "Thank you for joining the USChE community.",
        "We’ve built something special for you. Explore our resources!"
    ]
    salutations = ["Best regards,", "The USChE Team"]
    button_text = "Get Started"
    button_url = "https://usche.udom.ac.tz/dashboard"
    footer_text = "© 2026 USChE - University of Dodoma"

    # Call the Celery task
    send_email_task.delay(
        subject=subject,
        to=recipient,
        greeting=greeting,
        lines=lines,
        salutations=salutations,
        button_text=button_text,
        button_url=button_url,
        footer_text=footer_text
    )


# Run test
if __name__ == "__main__":
    send_test_email()
