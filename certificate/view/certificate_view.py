from concurrent.futures import ThreadPoolExecutor, as_completed
import io
from pathlib import Path
from uuid import UUID
import zipfile
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from certificate.models import Certificate
from certificate.serializers import CertificateUserListSerializer, CertificateResponseSerializer
from usche_app import settings
from user.models import User
from conference.models import Conference
from rest_framework.pagination import PageNumberPagination

from typing import List, cast
from django.http import FileResponse, HttpRequest
import logging

from user.serializers import UserResponseSerializer
from utils.document_generator import generate_certificate_pdf

logger = logging.getLogger(__name__)

class CertificateViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=["get"], url_path="download-certificates")
    def download_certificates(self, request: HttpRequest):
        try:
            conference_id = request.GET.get("conference_id")
            if not conference_id:
                return Response(
                    {"detail": "conference_id is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                conference = Conference.objects.get(pk=conference_id)
            except Conference.DoesNotExist:
                return Response(
                    {"detail": "Conference not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            zip_path = Path(settings.MEDIA_ROOT) / "certificates" / f"{conference.conference_id}.zip"
            if not zip_path.exists():
                return Response(
                    {"detail": "Certificates ZIP file not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            return FileResponse(
                open(zip_path, "rb"),
                as_attachment=True,
                filename=f"{conference.conference_name}_certificates.zip",
                content_type="application/zip"
            )

        except Exception as e:
            logger.error(f"Error downloading certificates: {e}", exc_info=True)
            return Response(
                {"detail": "An error occurred while downloading the certificates."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def issue_certificates(self, request: HttpRequest):
        try:
            conference_id = request.GET.get("conference_id")
            if not conference_id:
                return Response({"detail": "conference_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                conference = Conference.objects.get(pk=conference_id)
            except Conference.DoesNotExist:
                return Response({"detail": "Conference not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = CertificateUserListSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            user_ids: List[UUID] = serializer.validated_data['user_ids']
            users = User.objects.filter(user_id__in=user_ids)

            # Validate existing user_ids
            existing_user_ids = set(users.values_list("user_id", flat=True))
            missing_ids = set(user_ids) - existing_user_ids
            if missing_ids:
                return Response(
                    {"detail": f"Users not found: {', '.join(str(x) for x in missing_ids)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Filter users who already have certificates
            existing_cert_user_ids = set(
                Certificate.objects.filter(
                    user_id__in=user_ids, conference=conference
                ).values_list("user_id", flat=True)
            )

            # Only process new certificates
            users_to_create = [u for u in users if u.user_id not in existing_cert_user_ids]
            
            zip_buffer = io.BytesIO()
            
            # Define worker function for ThreadPoolExecutor
            def create_cert_and_pdf(u):
                cert = Certificate.objects.create(user=u, conference=conference)
                pdf_bytes = generate_certificate_pdf(user=u, conference=conference)
                if pdf_bytes:
                    cert.is_created = True
                    cert.save(update_fields=["is_created"])
                return u, pdf_bytes

            # Use ThreadPoolExecutor to generate PDFs concurrently
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(create_cert_and_pdf, u) for u in users_to_create]

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for future in as_completed(futures):
                        u, pdf_bytes = future.result()
                        if pdf_bytes:
                            filename = f"{u.first_name}_{u.last_name}_certificate.pdf"
                            zip_file.writestr(filename, pdf_bytes)

            zip_buffer.seek(0)
            
            return FileResponse(
                zip_buffer,
                as_attachment=True,
                filename="certificates.zip",
                content_type="application/zip"
            )

        except Exception as e:
            logger.error(f"Error generating certificates: {e}", exc_info=True)
            return Response(
                {"detail": "An error occurred while generating certificates."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def list_conference_certificates(self, request: HttpRequest):

        conference_id = request.GET.get("conference_id")
        search = request.GET.get("search")

        if not conference_id:
            return Response({"detail": "conference_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            try:
                Conference.objects.get(pk=conference_id)
            except Conference.DoesNotExist:
                return Response({"detail": "Conference not found."}, status=status.HTTP_404_NOT_FOUND)

            certificates = Certificate.certificates_by_conference_with_search(conference_id, search)
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(certificates, request)

            if page is not None:
                serializer = CertificateResponseSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = CertificateResponseSerializer(certificates, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving certificates: {e}", exc_info=True)
            return Response({"detail": "An error occurred while retrieving certificates."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"])
    def users_without_certificates(self, request: HttpRequest):
        conference_id = request.GET.get("conference_id")
        search = request.GET.get("search")

        if not conference_id:
            return Response({"detail": "conference_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            try:
                conference = Conference.objects.get(pk=conference_id)
            except Conference.DoesNotExist:
                return Response({"detail": "Conference not found."}, status=status.HTTP_404_NOT_FOUND)

            users = Certificate.users_without_certificate_for_conference(conference, search)
            paginator = PageNumberPagination()
            paginator.page_size = 3
            page = paginator.paginate_queryset(users, request)

            if page is not None:
                serializer = UserResponseSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = UserResponseSerializer(users, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving users without certificates: {e}", exc_info=True)
            return Response({"detail": "An error occurred while retrieving users."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)