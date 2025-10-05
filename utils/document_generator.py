import os
import logging
from io import BytesIO
import tempfile
import time
import base64
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from certificate.enums.cert_purpose import CertificatePurpose
from conference.models import Conference
from usche_app import settings
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    
    
def generate_certificate_pdf(user: User, conference: Conference, purpose=CertificatePurpose.ATTENDANCE.value):
    """
    Generates a certificate PDF with embedded fonts and images.

    Args:
        user (User): The user receiving the certificate.
        conference: Conference instance.
        purpose: CertificatePurpose value.

    Returns:
        bytes: The generated PDF content as byte stream, or None on failure.
    """
    try:
        # ------------------ Images ------------------
        background_path = (
            os.path.join(settings.MEDIA_ROOT, conference.certificate_background.name)
            if conference.certificate_background else None
        )
        image_dir = os.path.join(settings.MEDIA_ROOT, "usche")

        images = {
            "udom_logo": f"file://{os.path.abspath(os.path.join(image_dir, 'udom_logo.png'))}",
            "usche_logo": f"file://{os.path.abspath(os.path.join(image_dir, 'usche_logo.png'))}",
            "uhuru_na_umoja": f"file://{os.path.abspath(os.path.join(image_dir, 'uhuru_na_umoja.png'))}",
            "dvc_signature": f"file://{os.path.abspath(os.path.join(image_dir, 'dvc-arc-signature.png'))}",
            "dr_meremo_signature": f"file://{os.path.abspath(os.path.join(image_dir, 'dr-mreno-signature.png'))}",
            "certificate_background": f"file://{os.path.abspath(background_path)}" if background_path else None,
        }

        # ------------------ Fonts ------------------
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

        # ------------------ Purpose Text ------------------
        if purpose == CertificatePurpose.ATTENDANCE:
            purpose_text = "active participation"
        elif purpose == CertificatePurpose.PRESENTATION:
            purpose_text = "abstract presentation"
        else:
            purpose_text = "active participation"

        # ------------------ Full Name ------------------
        full_name = f"{user.title} {user.first_name} "
        if user.middle_name:
            full_name += f"{user.middle_name} "
        full_name += user.last_name

        html_content = render_to_string("certificate_template.html", {
            "full_name": full_name,
            "images": images,
            "font_face_overrides": font_face_overrides,
            "purpose_text": purpose_text,
        })

        # ------------------ Temp HTML ------------------
        temp_dir = settings.CHROMIUM_TEMP_DIR or "/tmp/chromium-temp"
        os.makedirs(temp_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile("w", suffix=".html", dir=temp_dir, delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(html_content)
            temp_html_path = os.path.abspath(tmp_file.name)

        # ------------------ Headless Chrome ------------------
        chrome_options = Options()
        chrome_options.add_argument("--headless=old")  # stable headless
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--allow-file-access-from-files")
        chrome_options.add_argument("--disable-web-security")

        driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get(f"file://{temp_html_path}")

            # Wait until body is loaded
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(1)  # extra delay for fonts/images

            # ------------------ Generate PDF ------------------
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