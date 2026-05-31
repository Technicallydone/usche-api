import os
import logging
from io import BytesIO
from pathlib import Path
import shutil
import stat
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
from utils.qr_code_generator import generate_badge_qr
from selenium.webdriver.support.ui import WebDriverWait
import tempfile

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
        purpose (CertificatePurpose): The purpose of the certificate.

    Returns:
        bytes: The generated PDF content as byte stream, or None on failure.
    """

    try:
        # -------------------------
        # Snap-safe images folder
        # -------------------------
        image_snap_dir = Path.home() / "tmp/usche_images"
        image_snap_dir.mkdir(parents=True, exist_ok=True)

        # -------------------------
        # Copy logo images
        # -------------------------
        logos = [
            "udom_logo.png",
            "usche_logo.png",
            "uhuru_na_umoja.png",
            "dvc-arc-signature.png",
            "dr-mreno-signature.png"
        ]
        for logo in logos:
            src_logo = Path(settings.MEDIA_ROOT) / "usche" / logo
            dst_logo = image_snap_dir / logo
            if src_logo.exists():
                shutil.copy(src_logo, dst_logo)

        # -------------------------
        # Copy certificate background if exists
        # -------------------------
        if conference.certificate_background:
            src_bg = Path(settings.MEDIA_ROOT) / conference.certificate_background.name
            dst_bg = image_snap_dir / src_bg.name
            if src_bg.exists():
                shutil.copy(src_bg, dst_bg)
                background_path = f"file://{dst_bg}"
            else:
                background_path = None
        else:
            background_path = None

        # -------------------------
        # Images dict
        # -------------------------
        images = {
            "udom_logo": f"file://{image_snap_dir}/udom_logo.png",
            "usche_logo": f"file://{image_snap_dir}/usche_logo.png",
            "uhuru_na_umoja": f"file://{image_snap_dir}/uhuru_na_umoja.png",
            "dvc_signature": f"file://{image_snap_dir}/dvc-arc-signature.png",
            "dr_meremo_signature": f"file://{image_snap_dir}/dr-mreno-signature.png",
            "certificate_background": background_path,
        }

        # -------------------------
        # Fonts
        # -------------------------
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

        # -------------------------
        # Purpose text
        # -------------------------
        if purpose == CertificatePurpose.ATTENDANCE:
            purpose_text = "Active Participation"
        elif purpose == CertificatePurpose.PRESENTATION:
            purpose_text = "Abstract Presentation"
        else:
            purpose_text = "Active Participation"

        # -------------------------
        # Render HTML
        # -------------------------
        html_content = render_to_string("certificate_template.html", {
            "full_name": f"{user.title}. {user.first_name} {user.middle_name + ' ' if user.middle_name else ''}{user.last_name}",
            "images": images,
            "font_face_overrides": font_face_overrides,
            "purpose_text": purpose_text,
        })

        # -------------------------
        # Temp folder for Chromium
        # -------------------------
        temp_dir = settings.CHROMIUM_TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)

        temp_html_path = os.path.join(temp_dir, f"cert_{uuid.uuid4().hex}.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        os.chmod(temp_html_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

        logger.info(f"Using temporary directory for Chrome: {temp_dir}")
        logger.info(f"Temporary HTML path: {temp_html_path}")

        # -------------------------
        # Chrome headless
        # -------------------------
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


def _format_full_name(user: User):
    """Formats user title and full name."""
    title = (user.title or "").rstrip(".")
    parts = []
    if title:
        parts.append(f"{title}.")
    parts.append(user.first_name)
    if user.middle_name:
        parts.append(user.middle_name)
    parts.append(user.last_name)
    return " ".join(p for p in parts if p)

def _department_str(user: User):
    """Retrieves department name from user model."""
    dept = getattr(user, "department", None)
    if not dept:
        return ""
    return getattr(dept, "name", None) or str(dept)

def generate_badge_pdf(user: User, conference: Conference):
    """
    Generates attendee badge PDF with QR code (vertical A6 layout).
    """
    work_dir = Path(tempfile.mkdtemp(prefix="usche_badge_"))
    temp_html_path = None
    driver = None

    try:
        # Copy logos to temp work directory
        for logo in ("udom_logo.png", "usche_logo.png", "uhuru_na_umoja.png"):
            src_logo = Path(settings.MEDIA_ROOT) / "usche" / logo
            if src_logo.exists():
                shutil.copy(src_logo, work_dir / logo)

        # Background image setup
        background_path = None
        if conference.id_badge_background:
            src_bg = Path(settings.MEDIA_ROOT) / conference.id_badge_background.name
            if src_bg.exists():
                dst_bg = work_dir / src_bg.name
                shutil.copy(src_bg, dst_bg)
                background_path = f"file://{dst_bg}"

        # QR Code generation (assuming generate_badge_qr returns BytesIO)
        qr_io = generate_badge_qr(user, conference)
        qr_path = work_dir / f"{user.user_id}_qr.png"
        qr_path.write_bytes(qr_io.getvalue())

        images = {
            "udom_logo": f"file://{work_dir}/udom_logo.png",
            "usche_logo": f"file://{work_dir}/usche_logo.png",
            "badge_background": background_path,
            "qr_code": f"file://{qr_path}",
        }

        # CSS Font Overrides
        static_fonts = os.path.join(settings.STATIC_ROOT, "fonts")
        font_face_overrides = f"""
        <style>
        @font-face {{
            font-family: "Raleway";
            src: url("file://{static_fonts}/Raleway/Raleway-VariableFont_wght.ttf") format("truetype");
        }}
        @font-face {{
            font-family: "Californian FB";
            src: url("file://{static_fonts}/californian-fb/californian-fb.ttf") format("truetype");
        }}
        </style>
        """

        # Cleanup conference name string to prevent metadata leaks (Version:0.9 etc)
        clean_conference_name = str(conference.conference_name).strip()

        context = {
            "font_face_overrides": font_face_overrides,
            "images": images,
            "conference_name": clean_conference_name,
            "conference_start_date": conference.start_date,
            "conference_end_date": conference.end_date,
            "theme": getattr(conference, "theme", "") or "",
            "venue": conference.venue_name,
            "full_name": _format_full_name(user),
            "department": _department_str(user),
            "affiliation": getattr(user, "affiliation", ""),
            "role": user.role.name if user.role else "Attendee",
            "registration_id": str(user.user_id),
        }

        html_content = render_to_string("badge_template.html", context)

        # Write HTML to temp file for Selenium
        temp_dir = settings.CHROMIUM_TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)
        temp_html_path = os.path.join(temp_dir, f"badge_{uuid.uuid4().hex}.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Selenium / Chrome PDF Generation
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--force-device-scale-factor=1")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"file://{temp_html_path}")

        # Wait for fonts and content to load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        pdf_params = {
            "printBackground": True,
            "landscape": False,
            "paperWidth": 4.13,    # 105mm
            "paperHeight": 5.83,   # 148mm
            "marginTop": 0,
            "marginBottom": 0,
            "marginLeft": 0,
            "marginRight": 0,
            "preferCSSPageSize": True,
        }

        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", pdf_params)

        return base64.b64decode(pdf_data["data"])

    except Exception as e:
        logger.error("Error generating badge PDF: %s", e, exc_info=True)
        return None

    finally:
        if driver:
            driver.quit()
        if temp_html_path and os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        shutil.rmtree(work_dir, ignore_errors=True)