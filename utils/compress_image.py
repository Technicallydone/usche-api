import io
import os
import tempfile
from typing import Any
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile

def compress_and_convert_to_webp(image: Any) -> InMemoryUploadedFile:
    img = Image.open(image)
    max_size_in_mb = 1.2

    temp_file_path = tempfile.mktemp(suffix=".webp")
    
    img.save(temp_file_path, format='WebP', quality=80)

    while os.path.getsize(temp_file_path) > max_size_in_mb * 1024 * 1024:
        img.save(temp_file_path, format='WebP', quality=75)

    with open(temp_file_path, 'rb') as f:
        img_data = f.read()

    img_io = io.BytesIO(img_data)
    img_io.seek(0)

    compressed_image = InMemoryUploadedFile(
        img_io, None, temp_file_path, 'image/webp', len(img_data), None
    )

    os.remove(temp_file_path)

    return compressed_image
