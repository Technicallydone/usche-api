from PIL import Image
from django.core.exceptions import ValidationError
from utils.compress_image import compress_and_convert_to_webp

def validate_image(image):
    try:
        img = Image.open(image)
        img.verify()
    except Exception as e:
        raise ValidationError(message="Invalid image file.")
    
    compressed_image = compress_and_convert_to_webp(image)
    
    return compressed_image
