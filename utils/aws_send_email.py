import os
import boto3
import logging
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from usche_app import settings
from utils.email_templates.usche_feedback import usche_feedback_template 

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Now your AWS variables from settings
AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_REGION = settings.AWS_SES_REGION_NAME

client = boto3.client(
    'ses',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def send_email(recipient, subject, html_body, text_body=None, attachment_path=None):
    logger.debug(f"Sending email to {recipient} with subject '{subject}'")
    
    try:
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = settings.AWS_SES_VERIFIED_EMAIL
        msg['To'] = recipient

        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))

        msg.attach(MIMEText(html_body, 'html'))

        if attachment_path:
            with open(attachment_path, 'rb') as f:
                part = MIMEApplication(f.read())
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                msg.attach(part)

        response = client.send_raw_email(
            Source=settings.AWS_SES_VERIFIED_EMAIL,
            Destinations=[recipient],
            RawMessage={'Data': msg.as_string()}
        )

        logger.info(f"Email sent! Message ID: {response['MessageId']}")

    except ClientError as e:
        logger.error(f"Error sending email: {e.response['Error']['Message']}")

if __name__ == "__main__":
    html_body = usche_feedback_template("Godfrey Mcharo")

    send_email(
        recipient="mcharoprofg23@gmail.com",
        subject="Thank you for attending USCHE Conference",
        html_body=html_body,
        text_body="Thank you for attending the USCHE Conference. Please provide feedback."
    )
