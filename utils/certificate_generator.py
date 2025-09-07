# from django.template.loader import get_template
# from django.conf import settings
# from xhtml2pdf import pisa
# from io import BytesIO
# from django.core.files.base import ContentFile
# import os

# def generate_certificate_pdf(certificate):
#     template = get_template("certificate_template.html")

#     html = template.render({
#         "user": certificate.user,
#         "event_name": certificate.event_name,
#         "start_date": certificate.start_date,
#         "end_date": certificate.end_date,
#         "location": certificate.location,
#         "issued_at": certificate.issued_at,
#     })

#     # Replace static URL with full path for background image
#     html = html.replace(
#         '/static/certificate_template.jpg',
#         os.path.join(settings.BASE_DIR, '/static/certificate_template.jpg')
#     )

#     result = BytesIO()
#     pisa_status = pisa.CreatePDF(src=html, dest=result)

#     if pisa_status.err:
#         return None

#     pdf_file = ContentFile(result.getvalue(), name=f"certificate_{certificate.id}.pdf")
#     return pdf_file

# utils.py
from django.conf import settings
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.core.files.base import ContentFile
import os

from django.contrib.staticfiles import finders


# Required for static files like background images
def link_callback(uri, rel):
    path = finders.find(uri.replace(settings.STATIC_URL, ""))
    if path:
        return path
    return uri


def generate_certificate_pdf(certificate):
    template = get_template("certificate_template.html")
    html = template.render({
        "user": certificate.user,
        "event_name": certificate.event_name,
        "start_date": certificate.start_date.strftime("%B %d, %Y"),
        "end_date": certificate.end_date.strftime("%B %d, %Y"),
        "location": certificate.location,
        "issued_at": certificate.issued_at.strftime("%B %d, %Y, %I:%M %p"),
    })

    result = BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html,
        dest=result,
        link_callback=link_callback  # <-- very important
    )

    if pisa_status.err:
        return None

    return ContentFile(result.getvalue(), name=f"certificate_{certificate.id}.pdf")
