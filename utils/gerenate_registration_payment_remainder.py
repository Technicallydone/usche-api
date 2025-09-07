import logging
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def generate_payment_reminder_pdf():
    """
    Generate PDF from the payment_reminder_template.html template.

    Returns:
        BytesIO: PDF file stream or None on failure.
    """
    try:
        html_content = render_to_string("payment_reminder_template.html", {})
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        if pisa_status.err:
            raise Exception("Error generating PDF from payment_reminder_template.html")
        pdf_buffer.seek(0)
        return pdf_buffer

    except Exception as e:
        logger.error(f"Failed to generate payment reminder PDF: {e}", exc_info=True)
        return None
