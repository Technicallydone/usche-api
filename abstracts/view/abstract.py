import base64
import logging
import os
from typing import cast
from django.http import  Http404, HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import action
from abstracts.models import Abstract
from abstracts.serializers import AbstractSubmissionSerializer, AbstractSerializer, RequestRetrieveSerializer
from theme.models import SubTheme
from usche_app import settings
from user.models import User
from django.db import transaction

logger = logging.getLogger(__name__)

class AbstractViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated,]
    
    @swagger_auto_schema(
        operation_description="Retrieve document for the authenticated user by providing document ID",
        operation_summary="Abstract document",
        method="get",
        tags=["Abstract"],
        responses={
            200: openapi.Response(
                description="Successfully retrieved document",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Document retrieved successfully"),
                        'file_content': openapi.Schema(type=openapi.TYPE_STRING, example="Base64 encoded content of the document")
                    }
                ),
            ),
            400: openapi.Response(
                description="Bad Request - Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid input")
                    }
                ),
            ),
            401: openapi.Response(
                description="Unauthorized - User must be authenticated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Authentication credentials were not provided")
                    }
                ),
            ),
            404: openapi.Response(
                description="Document not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Document with given id not found")
                    }
                ),
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'document_id',
                openapi.IN_PATH,
                description="The UUID of the document to retrieve",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='abstract-document/(?P<document_id>[^/]+)')
    def read_document(self, request: HttpRequest, document_id):
        if not request.user.is_authenticated:
            return Response(
                data={"detail": "Authentication credentials were not provided"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Fetch the Abstract with the given document_id
            abstract = Abstract.objects.get(abstract_id=document_id)
            
            # Get the file path
            document_filename = abstract.document.name
            document_path = os.path.join(settings.MEDIA_ROOT, document_filename)

            if not os.path.exists(document_path):
                raise Http404("Document not found")

            # Open the document and read it as binary data
            with open(document_path, 'rb') as doc_file:
                file_content = doc_file.read()

            # Encode the content as base64 (for easy handling in frontend)
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

            return Response(
                data={
                    "detail": "Document retrieved successfully",
                    "file_content": file_content_base64  # Send the base64 encoded content
                },
                status=status.HTTP_200_OK
            )

        except Abstract.DoesNotExist:
            logger.error(f"Document with id {document_id} not found.")
            return Response(data={"detail": "Document not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error while retrieving document: {e}")
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Retrieve abstract to view status and comment",
        operation_summary="Retrieve abstract",
        method="post",
        tags=["Abstract"],
        request_body=RequestRetrieveSerializer,
        responses={
            200: openapi.Response(
                description="Successfully retrieved",
                schema=AbstractSerializer()
            ),
            401: openapi.Response(
                description="Unauthorized - User must be authenticated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Authentication credentials were not provided")
                    }
                ),
            ),
            404: openapi.Response(
                description="Not Found - No abstract found for the user",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="You do not have any abstract submitted for this conference")
                    }
                ),
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred while retrieving the abstract")
                    }
                ),
            ),
        }
    )
    @action(detail=False, methods=['post'])
    def retrieve_abstract(self, request: HttpRequest):

        if not request.user.is_authenticated:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = cast(User, request.user)
        request_serializer = RequestRetrieveSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        try:
            abstract = Abstract.retrieve_abstract(user=user, conference_id=request_serializer.validated_data.get("conference_id"))
            
            
            if abstract is None:
                return Response(data={"detail": "You don't have any abstract for this conference"}, status=status.HTTP_404_NOT_FOUND)
            
            response_serializer = AbstractSerializer(abstract)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Abstract.DoesNotExist:
            return Response(
                {"detail": "You do not have any abstract submitted for this conference"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Abstract.MultipleObjectsReturned:
            logger.error(f"User {user.user_id} has multiple abstracts.")
            return Response(
                {"detail": "Multiple abstracts found. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error(f"Error while retrieving abstract for user {user.user_id}: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Submit abstract by providing necessary details like title, sub theme ID, content, keywords for the authenticated user",
        operation_summary="Abstract Submission",
        method="post",
        tags=["Abstract"],
        request_body=AbstractSubmissionSerializer,
        responses={
            201: openapi.Response(
                description="Successfully abstract saved",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
            ),
            400: openapi.Response(
                description="Bad Request - Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid input")
                    }
                ),
            ),
            401: openapi.Response(
                description="Unauthorized - User must be authenticated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Authentication credentials were not provided")
                    }
                ),
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred while submitting the abstract")
                    }
                ),
            ),
        }
    )
    @action(detail=False, methods=['post'])
    def submit_abstract(self, request: HttpRequest):

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = cast(User, request.user)

        serializer = AbstractSubmissionSerializer(data=request.data, context={'user': user})

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    sub_theme = SubTheme.get_sub_theme_by_id(sub_theme_id=serializer.validated_data.get("sub_theme"))
                    
                    if sub_theme.theme.conference.is_conference_outdated():
                        return Response(data={"detail": "We regret to inform you that the conference has already ended."}, status=status.HTTP_403_FORBIDDEN)

                    
                    if sub_theme.theme.conference.is_abstract_submission_deadline_reached():
                        return Response(data={"detail": "We regret to inform you that the deadline for submitting abstracts has passed."}, status=status.HTTP_403_FORBIDDEN)
                    
                    Abstract.create_abstract(
                        title=serializer.validated_data.get("title"),
                        content=serializer.validated_data.get("content"),
                        keywords=serializer.validated_data.get("keywords"),
                        sub_theme=sub_theme,
                        user=user,
                        document=serializer.validated_data.get("document"),
                        authors=serializer.validated_data.get("authors")
                    )
                    

                return Response(
                    {"detail": "Your abstract has been successfully submitted! Please wait while we verify your submission. Once verified, we will notify you via email with further instructions."},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Error while saving abstract: {e}")
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
