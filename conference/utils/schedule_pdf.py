import logging
import os
from io import BytesIO

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from conference.models import Conference

logger = logging.getLogger(__name__)


def get_pdf_image(path, width, height):
    """Loads an image for ReportLab and logs its status."""
    if os.path.exists(path):
        try:
            logger.info(f"PDF Generator: Found image at '{path}'")
            return Image(path, width=width, height=height)
        except Exception as e:
            logger.error(
                f"PDF Generator: Failed to render image at '{path}'. Error: {e}"
            )
            return ""
    else:
        logger.warning(f"PDF Generator: Image file NOT FOUND at path: '{path}'")
        return ""


def generate_schedule_pdf(conference: Conference, image_dir=None):
    """Generates a styled PDF schedule for a Conference instance."""
    buffer = BytesIO()

    # Set document with standard 0.5 inch margins
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"{conference.conference_name} Schedule",
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.5 * inch,
    )

    if image_dir is None:
        image_dir = os.path.join(settings.MEDIA_ROOT, "usche")

    # Image asset paths
    uhuru_logo_path = os.path.join(image_dir, "uhuru_na_umoja.png")
    udom_logo_path = os.path.join(image_dir, "udom_logo.png")
    usche_logo_path = os.path.join(image_dir, "usche_logo.png")

    # Load images
    uhuru_img = get_pdf_image(
        uhuru_logo_path, width=0.9 * inch, height=0.9 * inch
    )
    udom_img = get_pdf_image(
        udom_logo_path, width=0.9 * inch, height=0.9 * inch
    )
    usche_logo_img = get_pdf_image(
        usche_logo_path, width=0.8 * inch, height=0.8 * inch
    )

    styles = getSampleStyleSheet()

    # Base typography styles
    hdr_txt_style = ParagraphStyle(
        "HdrText",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=8.5,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1A202C"),
    )

    hdr_sub_style = ParagraphStyle(
        "HdrSub",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=8,
        leading=10,
        fontName="Helvetica",
        textColor=colors.HexColor("#4A5568"),
    )

    conf_title_style = ParagraphStyle(
        "ConfTitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=15,
        leading=19,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0D3B66"),
    )

    day_heading_style = ParagraphStyle(
        "DayHeading",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0D3B66"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    table_body_style = ParagraphStyle(
        "TableBody",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica",
        textColor=colors.HexColor("#2D3748"),
    )

    elements = []

    # ==========================================
    # 1. OFFICIAL INSTITUTIONAL HEADER
    # ==========================================

    header_text_cell = [
        Paragraph("THE UNITED REPUBLIC OF TANZANIA", hdr_txt_style),
        Paragraph(
            "MINISTRY OF EDUCATION, SCIENCE AND TECHNOLOGY", hdr_sub_style
        ),
        Paragraph("THE UNIVERSITY OF DODOMA", hdr_txt_style),
        Paragraph(
            "UDOM Scientific Conference on Health (USCHe)", hdr_txt_style
        ),
        Spacer(1, 2),
        Paragraph(
            "P.O. Box 395, Dodoma &nbsp;|&nbsp; Email: info.usche@udom.ac.tz",
            hdr_sub_style,
        ),
    ]

    header_table = Table(
        [[uhuru_img, header_text_cell, udom_img]],
        colWidths=[1.1 * inch, 5.07 * inch, 1.1 * inch],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ]
        )
    )

    elements.append(header_table)
    elements.append(Spacer(1, 6))

    # Divider Bar
    elements.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#0D3B66"),
            spaceBefore=0,
            spaceAfter=12,
        )
    )

    # ==========================================
    # 2. CONFERENCE DETAILS BANNER
    # ==========================================

    conf_info = [
        Paragraph(conference.conference_name.upper(), conf_title_style),
        Spacer(1, 4),
        Paragraph(
            f"<b>Venue:</b> {conference.venue_name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Dates:</b> {conference.start_date.strftime('%d %b %Y')} - {conference.end_date.strftime('%d %b %Y')}",
            ParagraphStyle(
                "SubBanner",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                fontSize=9,
                textColor=colors.HexColor("#4A5568"),
            ),
        ),
    ]

    banner_table = Table(
        [[conf_info, usche_logo_img]], colWidths=[6.47 * inch, 0.8 * inch]
    )
    banner_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )

    elements.append(banner_table)
    elements.append(Spacer(1, 12))

    # ==========================================
    # 3. SCHEDULE TABLES WITH PAGE BREAKS
    # ==========================================

    printable_width = pdf.width

    col_widths = [
        printable_width * 0.14,  # Time
        printable_width * 0.35,  # Activity
        printable_width * 0.16,  # Speaker
        printable_width * 0.15,  # Moderator
        printable_width * 0.10,  # Hall
        printable_width * 0.10,  # Type
    ]

    schedule_days = list(
        conference.schedule_days.prefetch_related("schedules").all()
    )

    for index, day in enumerate(schedule_days):
        # Insert a explicit PageBreak before every day starting from the 2nd day
        if index > 0:
            elements.append(PageBreak())

        day_title_str = (
            f"{day.title} &mdash; {day.date.strftime('%A, %d %B %Y')}"
        )
        if day.location:
            day_title_str += f" &nbsp;<font color='#718096' size='9'>(Location: {day.location})</font>"

        elements.append(Paragraph(day_title_str, day_heading_style))
        elements.append(Spacer(1, 6))

        headers = ["Time", "Activity", "Speaker", "Moderator", "Hall", "Type"]
        data = [[Paragraph(h, table_header_style) for h in headers]]

        for schedule in day.schedules.all():
            start_t = (
                schedule.start_time.strftime("%H:%M")
                if hasattr(schedule.start_time, "strftime")
                else str(schedule.start_time)[:5]
            )
            end_t = (
                schedule.end_time.strftime("%H:%M")
                if hasattr(schedule.end_time, "strftime")
                else str(schedule.end_time)[:5]
            )

            row = [
                Paragraph(f"{start_t} - {end_t}", table_body_style),
                Paragraph(schedule.activity or "-", table_body_style),
                Paragraph(schedule.speaker or "-", table_body_style),
                Paragraph(schedule.moderator or "-", table_body_style),
                Paragraph(schedule.hall or "-", table_body_style),
                Paragraph(
                    str(schedule.get_session_type_display())
                    if hasattr(schedule, "get_session_type_display")
                    else str(schedule.session_type or "-"),
                    table_body_style,
                ),
            ]
            data.append(row)

        table = Table(data, repeatRows=1, colWidths=col_widths)

        ts = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D3B66")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        for i in range(1, len(data)):
            if i % 2 == 0:
                ts.append(
                    ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F7FAFC"))
                )

        table.setStyle(TableStyle(ts))
        elements.append(table)

    pdf.build(elements)
    buffer.seek(0)

    return buffer