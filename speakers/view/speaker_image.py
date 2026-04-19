import os
from django.http import FileResponse, Http404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
import logging

from speakers.models import Speaker
from usche_app import settings

logger = logging.getLogger(__name__)

class SpeakerImageViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='speaker-image/(?P<image_id>[^/]+)')
    def speaker_image(self, request, image_id):
        try:
            # Retrieve the speaker object by speaker_id
            speaker_data = Speaker.objects.get(speaker_id=image_id)
            
            # Get the image filename directly from the speaker image field
            image_filename = speaker_data.speaker_image.name  # This gives the full path relative to MEDIA_ROOT
            image_path = os.path.join(settings.MEDIA_ROOT, image_filename)

            # Check if the image exists
            if not os.path.exists(image_path):
                raise Http404("Image not found")

            # Serve the image as a response
            return FileResponse(open(image_path, 'rb'), content_type="image/jpeg")

        except Speaker.DoesNotExist:
            logger.error(f"Speaker with id {image_id} not found.")
            return Response(data={"detail": "Speaker not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error while retrieving speaker image: {e}")
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
