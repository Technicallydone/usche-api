import base64
import logging
import os
from typing import cast
from rest_framework.request import Request

from django.http import FileResponse, Http404
from django.db import transaction

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from abstracts.enums.abstract_status import AbstractStatus
from abstracts.models import Abstract, AbstractAuthor
from abstracts.serializers import (
    AbstractSubmissionSerializer,
    AbstractSerializer,
    AbstractQuerySerializer,
    AbstractDecisionSerializer,
    MyAbstractQuerySerializer
)
from services.email.tasks import send_email_task
from themes.models import MainTheme
from themes.models import SubTheme
from usche_app import settings
from user.models import User
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)


class AbstractViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        'list': AppPermissionEnum.READ_ABSTRACT_ALL.value,
        'retrieve': [AppPermissionEnum.READ_ABSTRACT_ALL.value, AppPermissionEnum.READ_ABSTRACT_OWN.value],
        'read_document': AppPermissionEnum.READ_ABSTRACT.value,
        'mine': AppPermissionEnum.READ_ABSTRACT_OWN.value,
        'mine_by_id': AppPermissionEnum.READ_ABSTRACT_OWN.value,
        'submit_abstract': AppPermissionEnum.CREATE_ABSTRACT.value,
        'download_document': AppPermissionEnum.DOWNLOAD_ABSTRACT_DOCUMENT.value,
        'reject': AppPermissionEnum.APPROVE_ABSTRACT.value,
        'approve': AppPermissionEnum.REJECT_ABSTRACT.value,
        'create': AppPermissionEnum.CREATE_ABSTRACT.value
    }
    
    @action(detail=True, methods=["get"], url_path="mine")
    def mine_by_id(self, request: Request, pk=None):
        user = cast(User, request.user)

        try:
            abstract = Abstract.objects.get(
                pk=pk,
                user=user
            )

            serializer = AbstractSerializer(abstract)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Abstract.DoesNotExist:
            return Response(
                {"detail": "Abstract not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request: Request):
        user = cast(User, request.user)

        try:
            query_serializer = MyAbstractQuerySerializer(
                data=request.query_params,
            )
            query_serializer.is_valid(raise_exception=True)

            abstracts = Abstract.objects.filter(user=user)

            status_filter = query_serializer.validated_data.get("status")

            if status_filter:
                abstracts = abstracts.filter(status=status_filter)

            abstracts = abstracts.order_by("-created_at")

            paginator = PageNumberPagination()
            paginator.page_size_query_param = "page_size"

            page = paginator.paginate_queryset(abstracts, request)

            if page is not None:
                serializer = AbstractSerializer(page, many=True)

                return paginator.get_paginated_response(
                    serializer.data
                )

            serializer = AbstractSerializer(
                abstracts,
                many=True,
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(e, exc_info=True)

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def create(self, request: Request):
        user = cast(User, request.user)

        serializer = AbstractSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():

                sub_theme_id = serializer.validated_data.get("sub_theme")
                sub_theme = SubTheme.get_sub_theme_by_id(sub_theme_id=sub_theme_id)

                if not sub_theme:
                    return Response(
                        {"detail": "Invalid sub-theme selected."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not sub_theme.theme:
                    return Response(
                        {"detail": "Sub-theme is not linked to a valid theme."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                conference = sub_theme.theme.conference

                if conference.is_conference_outdated():
                    return Response(
                        {"detail": "Conference has already ended."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if conference.is_abstract_submission_deadline_reached():
                    return Response(
                        {"detail": "Abstract submission deadline has passed."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # -----------------------------------
                # CREATE ABSTRACT
                # -----------------------------------
                abstract = Abstract.objects.create(
                    title=serializer.validated_data.get("title"),
                    content=serializer.validated_data.get("content"),
                    keywords=serializer.validated_data.get("keywords"),
                    sub_theme=sub_theme,
                    user=user,
                    document=serializer.validated_data.get("document"),
                )

                # -----------------------------------
                # CREATE AUTHORS (IMPORTANT PART)
                # -----------------------------------
                authors_data = serializer.validated_data.get("authors", [])

                abstract_authors = [
                    AbstractAuthor(
                        abstract=abstract,
                        full_name=author["full_name"],
                        affiliation=author["affiliation"],
                        is_presenting_author=author.get("is_presenting_author", False),
                        order=author.get("order", idx),
                    )
                    for idx, author in enumerate(authors_data)
                ]

                AbstractAuthor.objects.bulk_create(abstract_authors)
                
                send_email_task.delay(
                    subject="Abstract Submission Received - USChE Conference",
                    to=user.email,
                    greeting=f"Hello {user.first_name},",
                    lines=[
                        "Thank you for submitting your abstract to the USChE Conference.",
                        "Your submission has been received successfully and is currently under review by the scientific committee.",
                        "You will be notified once the review process has been completed.",
                    ],
                    salutations=["Best regards,", "The USChE Scientific Committee"],
                    button_text="View Abstract",
                    button_url=f"{settings.FRONTEND_BASE_URL}/dashboard/abstracts/{abstract.abstract_id}",
                    footer_text="© 2026 USChE - University of Dodoma",
                )

            return Response(
                {
                    "detail": "Your abstract has been successfully submitted. We will notify you after verification.",
                    "id": str(abstract.abstract_id),
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(e, exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request: Request, pk=None):
        serializer = AbstractDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
                
        try:
            with transaction.atomic():
                abstract = Abstract.objects.select_for_update().get(pk=pk)
                
                if abstract.status != AbstractStatus.PENDING.value:
                    return Response(data={"detail": "Only pending abstracts can be modified."}, status=status.HTTP_400_BAD_REQUEST)

                abstract.status = AbstractStatus.REJECTED.value
                abstract.comment = serializer.validated_data.get("comment")
                abstract.save()

            logger.info(f"Abstract {pk} rejected by {request.user}")
            
            send_email_task.delay(
                subject="Abstract Submission Update - USChE Conference",
                to=abstract.user.email,
                greeting=f"Hello {abstract.user.first_name},",
                lines=[
                    "Thank you for submitting your abstract to the USChE Conference.",
                    "After careful review by the scientific committee, we regret to inform you that your abstract was not approved.",
                    f"Reviewer Comment: {serializer.validated_data.get('comment') or 'No additional comment was provided.'}",
                    "You may review the feedback and submit an improved version if submissions are still open.",
                ],
                salutations=["Best regards,", "The USChE Scientific Committee"],
                button_text="View Abstract",
                button_url=f"{settings.FRONTEND_BASE_URL}/dashboard/abstracts/{abstract.abstract_id}",
                footer_text="© 2026 USChE - University of Dodoma",
            )

            return Response(
                {"detail": "Abstract rejected successfully"},
                status=status.HTTP_200_OK,
            )

        except Abstract.DoesNotExist:
            return Response(
                {"detail": "Abstract not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error rejecting abstract {pk}: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request: Request, pk=None):
        try:
            with transaction.atomic():
                abstract = Abstract.objects.select_for_update().get(pk=pk)
                
                if abstract.status != AbstractStatus.PENDING.value:
                    return Response(data={"detail": "Only pending abstracts can be modified."}, status=status.HTTP_400_BAD_REQUEST)

                abstract.status = AbstractStatus.APPROVED.value
                abstract.comment = None
                abstract.save()

            logger.info(f"Abstract {pk} approved by {request.user}")
            
            send_email_task.delay(
                subject="Abstract Approved - USChE Conference",
                to=abstract.user.email,
                greeting=f"Hello {abstract.user.first_name},",
                lines=[
                    "We are pleased to inform you that your abstract has been approved by the USChE Scientific Committee.",
                    "Congratulations on your successful submission.",
                    "Please continue monitoring your dashboard for further conference updates and presentation guidelines.",
                ],
                salutations=["Best regards,", "The USChE Scientific Committee"],
                button_text="View Abstract",
                button_url=f"{settings.FRONTEND_BASE_URL}/dashboard/abstracts/{abstract.abstract_id}",
                footer_text="© 2026 USChE - University of Dodoma",
            )

            return Response(
                {"detail": "Abstract approved successfully"},
                status=status.HTTP_200_OK,
            )

        except Abstract.DoesNotExist:
            return Response(
                {"detail": "Abstract not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error approving abstract {pk}: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
    def retrieve(self, request: Request, pk=None):
        try:
            if pk is None:
                return Response(data={"detail": "Please select abstract"}, status=status.HTTP_400_BAD_REQUEST)
            
            abstract = Abstract.objects.get(pk=pk)

            serializer = AbstractSerializer(abstract)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Abstract.DoesNotExist:
            return Response(
                {"detail": "Abstract not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error retrieving abstract: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=True, methods=["get"], url_path="download-document")
    def download_document(self, request: Request, pk=None):
        try:
            abstract = Abstract.objects.get(pk=pk)

            document_path = abstract.document.path

            if not os.path.exists(document_path):
                raise Http404("Document not found")

            response = FileResponse(open(document_path, "rb"), as_attachment=True)

            filename = os.path.basename(document_path)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            return response

        except Abstract.DoesNotExist:
            return Response(
                {"detail": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def list(self, request: Request):
        serializer = AbstractQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        search = validated_data.get("search")
        abstractStatus = validated_data.get("status")

        try:
            main_theme = MainTheme.objects.get(conference__conference_id=validated_data.get('conference_id'))

            abstracts = Abstract.get_conference_abstracts(
                main_theme=main_theme,
                search_query=search,
                status=abstractStatus
            )

            paginator = PageNumberPagination()
            paginator.page_size_query_param = "page_size"

            page = paginator.paginate_queryset(abstracts, request)

            if page is not None:
                response_serializer = AbstractSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)

            response_serializer = AbstractSerializer(abstracts, many=True)

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        except MainTheme.DoesNotExist:
            return Response(
                {"detail": "Conference theme not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
    @action(detail=False, methods=["get"], url_path="abstract-document/(?P<document_id>[^/]+)")
    def read_document(self, request: Request, document_id):

        try:
            abstract = Abstract.objects.get(abstract_id=document_id)

            document_filename = abstract.document.name
            document_path = os.path.join(settings.MEDIA_ROOT, document_filename)

            if not os.path.exists(document_path):
                raise Http404("Document not found")

            with open(document_path, "rb") as doc_file:
                file_content = doc_file.read()

            file_content_base64 = base64.b64encode(file_content).decode("utf-8")

            return Response(
                {
                    "detail": "Document retrieved successfully",
                    "file_content": file_content_base64,
                },
                status=status.HTTP_200_OK,
            )

        except Abstract.DoesNotExist:
            logger.error(f"Document {document_id} not found.")
            return Response(
                {"detail": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

