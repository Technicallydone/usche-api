import os
from django.http import FileResponse, Http404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from sponsors.models import Sponsor
from usche_app import settings

logger = logging.getLogger(__name__)

class SponsorViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="View Sponsor image",
        operation_summary="Sponsor image",
        method="get",
        tags=["Sponsor"],
        responses={
            200: "Image response", 
            400: "Invalid input data",
            404: "Image not found"
        },
        manual_parameters=[
            openapi.Parameter(
                'image_id',
                openapi.IN_PATH,
                description="The UUID of the image to retrieve",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='sponsor-logo/(?P<image_id>[^/]+)')
    def sponsor_logo(self, request, image_id):
        try:
            # Retrieve the Sponsor object by Sponsor_id
            sponsor_data = Sponsor.objects.get(sponsor_id=image_id)
            
            # Get the image filename directly from the Sponsor image field
            image_filename = sponsor_data.logo.name  # This gives the full path relative to MEDIA_ROOT
            image_path = os.path.join(settings.MEDIA_ROOT, image_filename)

            # Check if the image exists
            if not os.path.exists(image_path):
                raise Http404("Image not found")

            # Serve the image as a response
            return FileResponse(open(image_path, 'rb'), content_type="image/jpeg")

        except Sponsor.DoesNotExist:
            logger.error(f"Sponsor with id {image_id} not found.")
            return Response(data={"detail": "Sponsor not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error while retrieving Sponsor image: {e}")
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
