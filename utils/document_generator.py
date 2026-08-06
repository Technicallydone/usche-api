import base64
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from django.template.loader import render_to_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from certificate.enums.cert_purpose import CertificatePurpose
from conference.models import Conference
from usche_app import settings
from user.models import User

logger = logging.getLogger(__name__)


def generate_invitation_pdf(user: User, conference: Conference):
    """
    Generates an invitation PDF letter using Headless Chrome CDP.

    Returns:
        bytes: The generated PDF content as a byte stream, or None on failure.
    """
    work_dir = Path(tempfile.mkdtemp(prefix="usche_invitation_"))
    temp_html_path = None
    driver = None

    try:
        # Copy assets to temporary isolated work directory
        image_dir = Path(settings.MEDIA_ROOT) / "usche"
        for logo in ("udom_logo.png", "usche_logo.png", "uhuru_na_umoja.png", "signature.png"):
            src_logo = image_dir / logo
            if src_logo.exists():
                shutil.copy(src_logo, work_dir / logo)

        images = {
            "udom_logo": f"file://{work_dir}/udom_logo.png",
            "usche_logo": f"file://{work_dir}/usche_logo.png",
            "uhuru_logo": f"file://{work_dir}/uhuru_na_umoja.png",
            "signature": f"file://{work_dir}/signature.png",
        }

        current_date = datetime.now().strftime("%d %B %Y")

        html_content = render_to_string("invitation_template.html", {
            "attendee": user,
            "date": current_date,
            "venue": conference.venue_name,
            "images": images,
            "title": user.title,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "conference_name": conference.conference_name,
        })

        # Save HTML to Chromium temp directory
        temp_dir = settings.CHROMIUM_TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)
        temp_html_path = os.path.join(temp_dir, f"invitation_{uuid.uuid4().hex}.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Setup Headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--force-device-scale-factor=1")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"file://{temp_html_path}")

        # Dynamic DOM wait
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Standard A4 PDF Output (8.27in x 11.69in)
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "landscape": False,
            "paperWidth": 8.27,
            "paperHeight": 11.69,
            "marginTop": 0.4,
            "marginBottom": 0.4,
            "marginLeft": 0.4,
            "marginRight": 0.4,
            "preferCSSPageSize": True,
        })

        return base64.b64decode(pdf_data["data"])

    except Exception as e:
        logger.error("Error generating invitation PDF: %s", e, exc_info=True)
        return None

    finally:
        if driver:
            driver.quit()
        if temp_html_path and os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        shutil.rmtree(work_dir, ignore_errors=True)


def generate_certificate_pdf(user: User, conference: Conference, purpose=CertificatePurpose.ATTENDANCE):
    """
    Generates a certificate PDF with embedded fonts and images using Headless Chrome CDP.

    Returns:
        bytes: The generated PDF content as a byte stream, or None on failure.
    """
    work_dir = Path(tempfile.mkdtemp(prefix="usche_cert_"))
    temp_html_path = None
    driver = None

    try:
        # Copy logos to isolated workspace
        logos = [
            "udom_logo.png",
            "usche_logo.png",
            "uhuru_na_umoja.png",
            "dvc-arc-signature.png",
            "dr-mreno-signature.png",
        ]
        for logo in logos:
            src_logo = Path(settings.MEDIA_ROOT) / "usche" / logo
            if src_logo.exists():
                shutil.copy(src_logo, work_dir / logo)

        # Copy background asset if available
        background_path = None
        if conference.certificate_background:
            src_bg = Path(settings.MEDIA_ROOT) / conference.certificate_background.name
            if src_bg.exists():
                dst_bg = work_dir / src_bg.name
                shutil.copy(src_bg, dst_bg)
                background_path = f"file://{dst_bg}"

        images = {
            "udom_logo": f"file://{work_dir}/udom_logo.png",
            "usche_logo": f"file://{work_dir}/usche_logo.png",
            "uhuru_na_umoja": f"file://{work_dir}/uhuru_na_umoja.png",
            "dvc_signature": f"file://{work_dir}/dvc-arc-signature.png",
            "dr_meremo_signature": f"file://{work_dir}/dr-mreno-signature.png",
            "certificate_background": background_path,
        }

        # Fonts configuration
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

        # Purpose mapping
        if purpose == CertificatePurpose.ATTENDANCE:
            purpose_text = "Active Participation"
        elif purpose == CertificatePurpose.PRESENTATION:
            purpose_text = "Abstract Presentation"
        else:
            purpose_text = "Active Participation"

        # Format full name cleanly
        middle = f" {user.middle_name}" if user.middle_name else ""
        full_name = f"{user.title}. {user.first_name}{middle} {user.last_name}"

        html_content = render_to_string("certificate_template.html", {
            "full_name": full_name,
            "images": images,
            "font_face_overrides": font_face_overrides,
            "purpose_text": purpose_text,
        })

        # Save HTML to Chromium temp directory
        temp_dir = settings.CHROMIUM_TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)
        temp_html_path = os.path.join(temp_dir, f"cert_{uuid.uuid4().hex}.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Setup Headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--force-device-scale-factor=1")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"file://{temp_html_path}")

        # Dynamic DOM wait
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # A4 Landscape dimensions (11.69in x 8.27in)
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "landscape": True,
            "paperWidth": 11.69,
            "paperHeight": 8.27,
            "marginTop": 0,
            "marginBottom": 0,
            "marginLeft": 0,
            "marginRight": 0,
            "preferCSSPageSize": True,
        })

        return base64.b64decode(pdf_data["data"])

    except Exception as e:
        logger.error("Error generating certificate PDF: %s", e, exc_info=True)
        return None

    finally:
        if driver:
            driver.quit()
        if temp_html_path and os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        shutil.rmtree(work_dir, ignore_errors=True)