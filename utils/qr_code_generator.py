import io
import qrcode

from conference.models import Conference
from usche_app import settings
from user.models import User

def generate_badge_qr(user: User, conference: Conference):
    verification_url = (
        f"{settings.FRONTEND_BASE_URL}/attendance/scanner"
        f"?user_id={user.user_id}"
        f"&conference_id={conference.conference_id}"
    )

    return generate_qr_code(verification_url)


def generate_qr_code(data: str) -> io.BytesIO:
    """
    Generates a QR code for the given data and returns it as a file-like object.
    
    Args:
        data (str): The data to encode in the QR code.
    
    Returns:
        io.BytesIO: File-like object containing the QR code image.
    """
    qr = qrcode.make(data)
    img_io = io.BytesIO()
    qr.save(img_io, format='PNG')
    img_io.seek(0) 
    return img_io