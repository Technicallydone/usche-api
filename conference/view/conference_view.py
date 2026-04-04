import mimetypes
import os
from django.http import FileResponse
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from conference.models import Conference
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from conference.serializers import (
    ConferenceSerailizer,
    ConferenceDetailSerializer
)
from usche_app import settings
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission
from rest_framework.request import Request
import logging

logger = logging.getLogger(__name__)

class ConferenceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    
    permission_mapping = {
        'list': AppPermissionEnum.READ_CONFERENCE.value,
        'retrieve': AppPermissionEnum.READ_CONFERENCE.value,
        'retrieve_certificat_template': AppPermissionEnum.READ_CONFERENCE.value
    }
    
    @action(detail=True, methods=['get'], url_path='certificate-template')
    def retrieve_certificat_template(self, request: Request, pk=None):
        if pk is None:
            return Response(
                {"detail": "No conference ID provided"},
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:
            conference = Conference.objects.get(conference_id=pk)

            if not conference.certificate_background:
                return Response(
                    {"detail": "No certificate template uploaded"},
                    status=status.HTTP_404_NOT_FOUND
                )

            file_path = conference.certificate_background.path

            if not os.path.exists(file_path):
                return Response(
                    {"detail": "Certificate template not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            content_type, _ = mimetypes.guess_type(file_path)

            return FileResponse(
                open(file_path, 'rb'),
                content_type=content_type or 'application/octet-stream'
            )

        except Conference.DoesNotExist:
            logger.error(f"Conference with id {pk} not found.")
            return Response(
                {"detail": "Conference not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"Error while retrieving conference certificate template: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request: Request):
        """List conferences with pagination and order by listing_date descending"""
        

        try:
            conferences = Conference.objects.all().order_by('-listing_date')

            paginator = PageNumberPagination()
            paginator.page_size_query_param = 'page_size'
            page = paginator.paginate_queryset(conferences, request)

            if page is not None:
                serializer = ConferenceSerailizer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = ConferenceSerailizer(conferences, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching conferences: {str(e)}")
            return Response({"detail": "Error fetching conferences"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request: Request, pk=None):
        """
        Retrieve a single conference by its primary key (conference_id)
        using the standard DRF retrieve method.
        """
        try:
            conference = Conference.objects.filter(conference_id=pk).first()
            if not conference:
                return Response({"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = ConferenceDetailSerializer(conference)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving conference {pk}: {str(e)}")
            return Response({"detail": "Error retrieving conference"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)