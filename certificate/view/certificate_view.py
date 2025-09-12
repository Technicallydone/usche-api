from concurrent.futures import ThreadPoolExecutor, as_completed
import io
from pathlib import Path
from uuid import UUID
import zipfile
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from certificate.models import Certificate
from certificate.serializers import CertificateUserListSerializer, CertificateResponseSerializer
from usche_app import settings
from user.enums.role import ROLE
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
    
    @swagger_auto_schema(
        method="get",
        operation_summary="Download Certificates ZIP",
        operation_description="Download the pre-generated certificates ZIP file for a given conference.",
        tags=["Certificates"],
        manual_parameters=[
            openapi.Parameter(
                name="conference_id",
                in_=openapi.IN_QUERY,
                description="UUID of the conference",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(description="ZIP file download."),
            400: openapi.Response(description="Missing or invalid conference_id."),
            401: openapi.Response(description="Unauthorized."),
            404: openapi.Response(description="ZIP file not found."),
            500: openapi.Response(description="Internal server error."),
        }
    )
    @action(detail=False, methods=["get"], url_path="download-certificates")
    def download_certificates(self, request: HttpRequest):
        try:
            user = cast(User, request.user)
            if not user.is_authenticated or user.role not in [
                ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value
            ]:
                return Response(
                    {"detail": "You are not authorized to perform this task"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

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

    @swagger_auto_schema(
        method="post",
        operation_summary="Generate Certificates",
        operation_description="Generate certificates for a given conference and list of user IDs. Users who already have certificates for the conference will be skipped.",
        tags=["Certificates"],
        manual_parameters=[
            openapi.Parameter(
                name="conference_id",
                in_=openapi.IN_QUERY,
                description="UUID of the conference",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, format="uuid")
                )
            },
            required=["user_ids"]
        ),
        responses={
            201: openapi.Response(description="Certificates created successfully."),
            400: openapi.Response(description="Invalid input."),
            401: openapi.Response(description="Unauthorized."),
            500: openapi.Response(description="Internal server error."),
        }
    )
    @action(detail=False, methods=["post"])
    def issue_certificates(self, request: HttpRequest):
        try:
            user = cast(User, request.user)

            if not user.is_authenticated or user.role not in [
                ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value
            ]:
                return Response(
                    {"detail": "You are not authorized to perform this task"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

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


    @swagger_auto_schema(
        method="get",
        operation_summary="Get Certificates by Conference",
        operation_description="Retrieve all certificates issued for a specific conference. Supports optional search by user full name. Only accessible by authorized users.",
        tags=["Certificates"],
        manual_parameters=[
            openapi.Parameter(
                name="conference_id",
                in_=openapi.IN_QUERY,
                description="UUID of the conference",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                description="Optional search term to filter certificates by user full name",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Certificates retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'certificate_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'issued_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                                    'is_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'user': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                            'country': openapi.Schema(type=openapi.TYPE_STRING),
                                            'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                                            'affiliation': openapi.Schema(type=openapi.TYPE_STRING),
                                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                        }
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request - Missing or invalid conference_id.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="conference_id is required.")
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found - Conference does not exist.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Conference not found.")
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized - Must be authenticated and have appropriate role.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="You are not authorized to perform this task.")
                    }
                )
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred while retrieving certificates.")
                    }
                )
            ),
        }
    )
    @action(detail=False, methods=["get"])
    def list_conference_certificates(self, request: HttpRequest):
        user = cast(User, request.user)

        if not user.is_authenticated or user.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
            return Response(
                {"detail": "You are not authorized to perform this task."},
                status=status.HTTP_401_UNAUTHORIZED
            )

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


    @swagger_auto_schema(
        method="get",
        operation_summary="Get Users Without Certificates for Conference",
        operation_description="Retrieve all users who do not have a certificate for the specified conference. Supports optional search by full name. Only accessible by authorized users.",
        tags=["Certificates"],
        manual_parameters=[
            openapi.Parameter(
                name="conference_id",
                in_=openapi.IN_QUERY,
                description="UUID of the conference",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                description="Optional search term to filter users by full name",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Users retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                                    'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                    'country': openapi.Schema(type=openapi.TYPE_STRING),
                                    'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                                    'affiliation': openapi.Schema(type=openapi.TYPE_STRING),
                                    'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request - Missing or invalid conference_id.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="conference_id is required.")
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found - Conference does not exist.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Conference not found.")
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized - Must be authenticated and have appropriate role.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="You are not authorized to perform this task.")
                    }
                )
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred while retrieving users.")
                    }
                )
            ),
        }
    )
    @action(detail=False, methods=["get"])
    def users_without_certificates(self, request: HttpRequest):
        user = cast(User, request.user)

        if not user.is_authenticated or user.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
            return Response(
                {"detail": "You are not authorized to perform this task."},
                status=status.HTTP_401_UNAUTHORIZED
            )

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