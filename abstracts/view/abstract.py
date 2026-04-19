import base64
import logging
import os
from typing import cast
from rest_framework.request import Request

from django.http import Http404, HttpRequest
from django.db import transaction

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from abstracts.models import Abstract
from abstracts.serializers import (
    AbstractSubmissionSerializer,
    AbstractSerializer,
    AbstractQuerySerializer
)
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
        "read_document": AppPermissionEnum.READ_ABSTRACT_ALL.value,
        "mine": AppPermissionEnum.READ_ABSTRACT_OWN.value,
        "submit_abstract": AppPermissionEnum.CREATE_ABSTRACT.value,
    }
    
    def list(self, request: Request):
        serializer = AbstractQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        search = validated_data.get("search")

        try:
            main_theme = MainTheme.objects.get(conference__conference_id=validated_data.get('conference_id'))

            abstracts = Abstract.get_conference_abstracts(
                main_theme=main_theme,
                search_query=search,
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
    def read_document(self, request: HttpRequest, document_id):

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

    # 👤 Get current user's abstract
    @action(detail=False, methods=["post"])
    def mine(self, request: HttpRequest):

        user = cast(User, request.user)

        try:
            abstract = Abstract.retrieve_abstract(user=user)

            if abstract is None:
                return Response(
                    {"detail": "You don't have any abstract for this conference"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = AbstractSerializer(abstract)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Abstract.DoesNotExist:
            return Response(
                {"detail": "No abstract found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Abstract.MultipleObjectsReturned:
            logger.error(f"User {user.user_id} has multiple abstracts.")
            return Response(
                {"detail": "Multiple abstracts found. Contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            logger.error(f"Error retrieving abstract: {e}")
            return Response(
                {"detail": "Unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def submit_abstract(self, request: HttpRequest):

        user = cast(User, request.user)

        serializer = AbstractSubmissionSerializer(
            data=request.data,
            context={"user": user},
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():

                sub_theme = SubTheme.get_sub_theme_by_id(
                    sub_theme_id=serializer.validated_data.get("sub_theme")
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

                Abstract.create_abstract(
                    title=serializer.validated_data.get("title"),
                    content=serializer.validated_data.get("content"),
                    keywords=serializer.validated_data.get("keywords"),
                    sub_theme=sub_theme,
                    user=user,
                    document=serializer.validated_data.get("document"),
                    authors=serializer.validated_data.get("authors"),
                )

            return Response(
                {
                    "detail": (
                        "Your abstract has been successfully submitted. "
                        "We will notify you after verification."
                    )
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error submitting abstract: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )