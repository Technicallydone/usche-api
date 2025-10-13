import os
import logging
from io import BytesIO
import tempfile
import time
import base64
import uuid
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from certificate.enums.cert_purpose import CertificatePurpose
from conference.models import Conference
from usche_app import settings
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from user.models import User

logger = logging.getLogger(__name__)


def generate_invitation_pdf(user: User, conference: Conference):
    """
    Generates a PDF invitation letter with embedded images.

    Args:
        attendee (Attendee): The attendee receiving the invitation.

    Returns:
        BytesIO: The generated PDF file as a byte stream.
    """
    try:
        image_dir = os.path.join(settings.MEDIA_ROOT, "usche")
        images = {
            "udom_logo": os.path.join(image_dir, "udom_logo.png"),
            "usche_logo": os.path.join(image_dir, "usche_logo.png"),
            "uhuru_logo": os.path.join(image_dir, "uhuru_na_umoja.png"),
            "signature": os.path.join(image_dir, "signature.png")
        }
        
        current_date = datetime.now().strftime("%d %B %Y") 

        # Render HTML template
        html_content = render_to_string("invitation_template.html", {
            "attendee": user,
            "date": current_date,
            "venue": conference.venue_name,
            "images": images,
            "title": user.title,
            "last_name": user.last_name,
            "email": user.email,
            "conference_name": conference.conference_name,
        })

        # Convert HTML to PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        if pisa_status.err:
            raise Exception("Error generating PDF")
        pdf_buffer.seek(0)

        return pdf_buffer

    except Exception as e:
        logger.error(f"Error generating invitation PDF: {e}")
        return None
    
    
def generate_certificate_pdf(user: User, conference: Conference, purpose=CertificatePurpose.ATTENDANCE):
    """
    Generates a certificate PDF with embedded fonts and images.

    Args:
        user (User): The user receiving the certificate.
        conference (Conference): The conference details.

    Returns:
        bytes: The generated PDF content as byte stream.
    """
    try:
        # Prepare background and image paths
        background_path = (
            os.path.join(settings.MEDIA_ROOT, conference.certificate_background.name)
            if conference.certificate_background else None
        )
        image_dir = os.path.join(settings.MEDIA_ROOT, "usche")

        images = {
            "udom_logo": f"file://{os.path.join(image_dir, 'udom_logo.png')}",
            "usche_logo": f"file://{os.path.join(image_dir, 'usche_logo.png')}",
            "uhuru_na_umoja": f"file://{os.path.join(image_dir, 'uhuru_na_umoja.png')}",
            "dvc_signature": f"file://{os.path.join(image_dir, 'dvc-arc-signature.png')}",
            "dr_meremo_signature": f"file://{os.path.join(image_dir, 'dr-mreno-signature.png')}",
            "certificate_background": f"file://{background_path}" if background_path else None,
        }

        static_fonts = os.path.join(settings.STATIC_ROOT, "fonts")
        font_face_overrides = f"""
        <style>
        @font-face {{
            font-family: "Raleway";
            src: url("file://{static_fonts}/Raleway/Raleway-VariableFont_wght.ttf") format("truetype");
            font-weight: 100 900;
            font-style: normal;
        }}
        @font-face {{
            font-family: "Raleway";
            src: url("file://{static_fonts}/Raleway/Raleway-Italic-VariableFont_wght.ttf") format("truetype");
            font-weight: 100 900;
            font-style: italic;
        }}
        @font-face {{
            font-family: "Monotype Corsiva";
            src: url("file://{static_fonts}/Monotype-Corsiva/Monotype-Corsiva-Regular-Italic.ttf") format("truetype");
            font-style: italic;
            font-weight: normal;
        }}
        @font-face {{
            font-family: "Californian FB";
            src: url("file://{static_fonts}/californian-fb/californian-fb.ttf") format("truetype");
            font-style: normal;
            font-weight: normal;
        }}
        </style>
        """

        if purpose == CertificatePurpose.ATTENDANCE:
            purpose_text = "Active Participation"
        elif purpose == CertificatePurpose.PRESENTATION:
            purpose_text = "Abstract Presentation"
        else:
            purpose_text = "Active Participation"

        html_content = render_to_string("certificate_template.html", {
            "full_name": f"{user.title}. {user.first_name} {user.middle_name + ' ' if user.middle_name else ''}{user.last_name}",
            "images": images,
            "font_face_overrides": font_face_overrides,
            "purpose_text": purpose_text,
        })

        temp_dir = settings.CHROMIUM_TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)

        temp_html_path = os.path.join(temp_dir, f"cert_{uuid.uuid4().hex}.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Using temporary directory for Chrome: {temp_dir}")
        logger.info(f"Temporary HTML path: {temp_html_path}")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get(f"file://{temp_html_path}")
            time.sleep(2)

            paper_width = 794 / 96
            paper_height = 1123 / 96

            pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,
                "landscape": False,
                "paperWidth": paper_height,
                "paperHeight": paper_width,
                "marginTop": 0,
                "marginBottom": 0,
                "marginLeft": 0,
                "marginRight": 0,
            })

        finally:
            driver.quit()
            if os.path.exists(temp_html_path):
                os.remove(temp_html_path)

        return base64.b64decode(pdf_data["data"])

    except Exception as e:
        logger.error(f"Error generating certificate PDF: {e}", exc_info=True)
        return None