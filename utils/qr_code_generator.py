import io
import qrcode


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