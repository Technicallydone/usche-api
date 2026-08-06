import logging
import os
from io import BytesIO
from typing import Optional

from django.conf import settings
from django.db.models import Prefetch

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from conference.models import Conference
from feedback.enums.question_type import QuestionTypeEnum
from feedback.models import Question, FeedbackAnswer

logger = logging.getLogger(__name__)


def get_pdf_image(path: str, width: float, height: float):
    """Helper to safely load images for ReportLab without breaking if missing."""
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


def generate_feedback_report_pdf(
    conference: Optional[Conference] = None,
    created_from=None,
    created_to=None,
    image_dir: Optional[str] = None,
) -> BytesIO:
    """
    Generates an institutional PDF Feedback Evaluation Report for USCHe.
    
    Flows content naturally across pages using KeepTogether to keep question 
    titles and their respective summary tables on the same page.
    """
    buffer = BytesIO()

    doc_title = (
        f"{conference.conference_name} Feedback Report"
        if conference
        else "Overall Feedback Report"
    )

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=doc_title,
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

    # Typography styles
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

    report_title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0D3B66"),
    )

    question_title_style = ParagraphStyle(
        "QuestionTitle",
        parent=styles["Heading2"],
        fontSize=10,
        leading=13,
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

    meta_text_style = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#718096"),
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
    # 2. REPORT BANNER & FILTERS METADATA
    # ==========================================
    subtitle_parts = []
    if conference:
        subtitle_parts.append(f"<b>Conference:</b> {conference.conference_name}")
    else:
        subtitle_parts.append("<b>Scope:</b> All Conferences")

    date_filter_str = ""
    if created_from and created_to:
        date_filter_str = f"{created_from.strftime('%d %b %Y')} to {created_to.strftime('%d %b %Y')}"
    elif created_from:
        date_filter_str = f"From {created_from.strftime('%d %b %Y')}"
    elif created_to:
        date_filter_str = f"Until {created_to.strftime('%d %b %Y')}"

    if date_filter_str:
        subtitle_parts.append(f"<b>Filter Period:</b> {date_filter_str}")

    conf_info = [
        Paragraph("FEEDBACK EVALUATION REPORT", report_title_style),
        Spacer(1, 4),
        Paragraph(
            " &nbsp;&nbsp;|&nbsp;&nbsp; ".join(subtitle_parts),
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
    elements.append(Spacer(1, 14))

    # ==========================================
    # 3. QUERY DATA & PREFETCH
    # ==========================================
    question_filters = {}
    if conference:
        question_filters["conference"] = conference

    answer_filters = {}
    if created_from:
        answer_filters["submitted_at__gte"] = created_from
    if created_to:
        answer_filters["submitted_at__lte"] = created_to

    answers_qs = (
        FeedbackAnswer.objects.filter(**answer_filters)
        if answer_filters
        else FeedbackAnswer.objects.all()
    )

    questions = (
        Question.objects.filter(**question_filters)
        .prefetch_related(
            "options",
            Prefetch("answers", queryset=answers_qs),
            Prefetch("answers__option"),
        )
        .order_by("position")
    )

    printable_width = pdf.width

    # ==========================================
    # 4. RENDER QUESTIONS (USING KeepTogether)
    # ==========================================
    if not questions.exists():
        elements.append(
            Paragraph("No feedback questions available.", table_body_style)
        )
    else:
        for idx, q in enumerate(questions):
            question_block = []  # Group elements for this question

            answers = list(q.answers.all())
            total_responses = len(answers)

            # Question Header
            q_header = (
                f"Q{idx + 1}. {q.question} "
                f"<font color='#718096' size='8'>({total_responses} response{'s' if total_responses != 1 else ''})</font>"
            )
            question_block.append(Paragraph(q_header, question_title_style))
            question_block.append(Spacer(1, 6))

            # MULTIPLE CHOICE QUESTIONS
            if q.type == QuestionTypeEnum.MULTIPLE_CHOICE.value:
                col_widths = [
                    printable_width * 0.50,  # Option
                    printable_width * 0.15,  # Count
                    printable_width * 0.35,  # Percentage Breakdown
                ]

                table_data = [
                    [
                        Paragraph("Option", table_header_style),
                        Paragraph("Count", table_header_style),
                        Paragraph("Percentage", table_header_style),
                    ]
                ]

                for opt in q.options.all():
                    opt_count = sum(1 for a in answers if a.option_id == opt.id)
                    pct = (
                        (opt_count / total_responses * 100)
                        if total_responses > 0
                        else 0.0
                    )

                    pct_str = f"{pct:.1f}% ({opt_count}/{total_responses})"

                    table_data.append(
                        [
                            Paragraph(opt.option, table_body_style),
                            Paragraph(str(opt_count), table_body_style),
                            Paragraph(pct_str, table_body_style),
                        ]
                    )

                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                ts = [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D3B66")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
                for r_idx in range(1, len(table_data)):
                    if r_idx % 2 == 0:
                        ts.append(
                            (
                                "BACKGROUND",
                                (0, r_idx),
                                (-1, r_idx),
                                colors.HexColor("#F7FAFC"),
                            )
                        )
                table.setStyle(TableStyle(ts))
                question_block.append(table)

            # TEXT / OPEN-ENDED QUESTIONS
            else:
                text_answers = [a.text.strip() for a in answers if a.text and a.text.strip()]

                if not text_answers:
                    question_block.append(
                        Paragraph(
                            "<i>No written responses provided.</i>",
                            meta_text_style,
                        )
                    )
                else:
                    col_widths = [printable_width * 0.08, printable_width * 0.92]
                    table_data = [
                        [
                            Paragraph("#", table_header_style),
                            Paragraph("Response Text", table_header_style),
                        ]
                    ]

                    for t_idx, txt in enumerate(text_answers, start=1):
                        table_data.append(
                            [
                                Paragraph(str(t_idx), table_body_style),
                                Paragraph(txt, table_body_style),
                            ]
                        )

                    table = Table(table_data, colWidths=col_widths, repeatRows=1)
                    ts = [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D3B66")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ]
                    for r_idx in range(1, len(table_data)):
                        if r_idx % 2 == 0:
                            ts.append(
                                (
                                    "BACKGROUND",
                                    (0, r_idx),
                                    (-1, r_idx),
                                    colors.HexColor("#F7FAFC"),
                                )
                            )
                    table.setStyle(TableStyle(ts))
                    question_block.append(table)

            question_block.append(Spacer(1, 14))

            # Keep title and table together to prevent orphan headings at bottom of pages
            elements.append(KeepTogether(question_block))

    pdf.build(elements)
    buffer.seek(0)
    return buffer