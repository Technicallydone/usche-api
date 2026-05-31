import os
import uuid
import shutil
import base64
import logging
import tempfile
from pathlib import Path
from django.conf import settings
from django.template.loader import render_to_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from conference.models import Conference
from user.models import User
from utils.qr_code_generator import generate_badge_qr

logger = logging.getLogger(__name__)

def _format_full_name(user: User):
    """Formats attendee title and full name."""
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
    """Safely retrieves department or affiliation info."""
    dept = getattr(user, "department", None)
    if not dept:
        return ""
    return getattr(dept, "name", None) or str(dept)

def generate_badge_pdf(user: User, conference: Conference):
    """
    Generates attendee badge PDF with QR code using a vertical A6 layout.
    """
    work_dir = Path(tempfile.mkdtemp(prefix="usche_badge_"))
    temp_html_path = None
    driver = None
    
    try:
        # Copy assets to temporary work directory
        for logo in ("udom_logo.png", "usche_logo.png", "uhuru_na_umoja.png"):
            src_logo = Path(settings.MEDIA_ROOT) / "usche" / logo
            if src_logo.exists():
                shutil.copy(src_logo, work_dir / logo)

        # Background image setup (if provided)
        background_path = None
        if conference.id_badge_background:
            src_bg = Path(settings.MEDIA_ROOT) / conference.id_badge_background.name
            if src_bg.exists():
                dst_bg = work_dir / src_bg.name
                shutil.copy(src_bg, dst_bg)
                background_path = f"file://{dst_bg}"

        # QR Code setup
        qr_io = generate_badge_qr(user, conference)
        qr_path = work_dir / f"{user.user_id}_qr.png"
        qr_path.write_bytes(qr_io.getvalue())

        images = {
            "udom_logo": f"file://{work_dir}/udom_logo.png",
            "usche_logo": f"file://{work_dir}/usche_logo.png",
            "badge_background": background_path,
            "qr_code": f"file://{qr_path}",
        }

        # Dynamic Font Loading
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

        # FIX: Ensure conference_name is a clean string to prevent metadata leaks
        clean_name = str(conference.conference_name).strip()

        context = {
            "font_face_overrides": font_face_overrides,
            "images": images,
            "conference_name": clean_name,
            "conference_start_date": conference.start_date,
            "conference_end_date": conference.end_date,
            "theme": getattr(conference, "theme", "") or "",
            "venue": conference.venue_name,
            "full_name": _format_full_name(user),
            "department": _department_str(user),
            "affiliation": getattr(user, "affiliation", ""),
            "role": "Organizer" if user.is_staff else "Attendee",
            "registration_id": str(user.user_id),
        }

        html_content = render_to_string("badge_template.html", context)

        # Chrome/Selenium Setup
        temp_dir = settings.CHROMIUM_TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)
        temp_html_path = os.path.join(temp_dir, f"badge_{uuid.uuid4().hex}.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--force-device-scale-factor=1")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"file://{temp_html_path}")

        # Wait for full rendering
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # PDF output tailored to 105mm x 148mm (A6)
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "landscape": False,
            "paperWidth": 4.13,
            "paperHeight": 5.83,
            "marginTop": 0,
            "marginBottom": 0,
            "marginLeft": 0,
            "marginRight": 0,
            "preferCSSPageSize": True,
        })

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