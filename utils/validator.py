from django.core.exceptions import ValidationError
from datetime import date
import re
import os
from rest_framework import serializers
from PIL import Image

def validate_phone_number(value: str):
    """
    Validates a phone number format.
    
    - Supports international (+1234567890) and national (1234567890) formats.
    - Must start with a '+' for international numbers.
    - Only digits, spaces, dashes, and parentheses are allowed in appropriate positions.
    """
    pattern = re.compile(r'^\+?[1-9]\d{0,2}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}$')

    if not pattern.fullmatch(value):
        raise ValidationError("Invalid phone number format.")
    

# Custom validator function to ensure the date is in the future
def validate_future_date(value):
    if value <= date.today():
        raise ValidationError('The conference date must be in the future.')
    

def validate_document_type(file):
    """
    Validates the uploaded document's file type.
    Only allows PDF, DOCX, DOC files.
    """
    allowed_extensions = ['pdf', 'docx', 'doc', 'txt']
    extension = file.name.split('.')[-1].lower()
    
    if extension not in allowed_extensions:
        raise ValidationError(f"Invalid file type. Only {', '.join(allowed_extensions)} are allowed.")
    
    
def validate_pdf_document(file):
    """
    Validates the uploaded document's file type.
    Only allows PDF files.
    """
    allowed_extensions = ['pdf']
    extension = file.name.split('.')[-1].lower()
    
    if extension not in allowed_extensions:
        raise ValidationError(f"Invalid file type. Only {', '.join(allowed_extensions)} are allowed.")
    

def validate_svg(file):
    ext = os.path.splitext(file.name)[1].lower()
    
    if ext != ".svg":
        raise serializers.ValidationError("Only SVG files are allowed.")
    
    if file.content_type not in ["image/svg+xml"]:
        raise serializers.ValidationError("Invalid SVG file.")
    
    return file

def validate_image_file(file):
    try:
        image = Image.open(file)
        image.verify()
    except Exception:
        raise serializers.ValidationError("Invalid image file.")

    if image.format not in ["JPEG", "PNG", "WEBP"]:
        raise serializers.ValidationError(
            "Only JPEG, PNG, or WEBP images are allowed."
        )

    file.seek(0)

    return file