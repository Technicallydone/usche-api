import logging
from typing import cast
from django.http import  HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import action
from abstracts.enums.abstract_status import AbstractStatus
from abstracts.models import Abstract
from abstracts.serializers import AbstractSerializer, AbstractStatusUpdateSerializer, QRCodeVerificationSerializer, PaidAbstractSerializer
from attendee.model.attendee import Attendee
from conference.models import Conference
from theme.models import MainTheme
from user.enums.role import ROLE
from user.model.user import User
from utils.send_email import send_rejection_email
from django.db import transaction
from rest_framework.pagination import PageNumberPagination


logger = logging.getLogger(__name__)

class OrganizerAbstractViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated,]
    
    @swagger_auto_schema(
        operation_description="Retrieve abstract for the organizer",
        operation_summary="Retrieve Abstract for Organizer",
        method="post",
        tags=["Abstract"],
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
                description="Not Found - No abstract found",
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
        },
        manual_parameters=[
            openapi.Parameter(
                'abstract_id',
                openapi.IN_QUERY,
                description="The UUID of the abstract to retrieve",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'conference_id',
                openapi.IN_QUERY,
                description="The UUID of the abstract to retrieve",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def retrieve_abstract_info(self, request: HttpRequest):
        user = cast(User, request.user)

        if not request.user.is_authenticated and user.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        conference_id = request.GET.get("conference_id")
        if not conference_id:
            return Response(
                data={"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            
        abstract_id = request.GET.get("abstract_id")
        if not abstract_id:
            return Response(
                data={"detail": "Abstract ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )


        try:
            abstract = Abstract.retrieve_abstract(conference_id=conference_id, abstract_id=abstract_id)
            
            
            if abstract is None:
                return Response(data={"detail": "Abstract not found"}, status=status.HTTP_404_NOT_FOUND)
            
            response_serializer = AbstractSerializer(abstract)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Abstract.MultipleObjectsReturned:
            logger.error(f"multiple abstracts.")
            return Response(
                {"detail": "Multiple abstracts found. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error(f"Error while retrieving abstract: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Verify a QR code",
        operation_summary="Verify QR Code",
        method="post",
        tags=["QR Code"],
        request_body=QRCodeVerificationSerializer,
        responses={
            200: openapi.Response(
                description="User authenticated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="User John Doe authenticated for Conference XYZ")
                    }
                ),
            ),
            400: openapi.Response(
                description="Invalid QR Code or missing data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid QR Code")
                    }
                ),
            ),
            404: openapi.Response(
                description="User or Conference not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="User or Conference not found")
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
        }
    )
    @action(detail=False, methods=['post'])
    def verify_qr_code(self, request: HttpRequest):
        organizer = cast(User, request.user)

        if not request.user.is_authenticated and organizer.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = QRCodeVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        qr_data = serializer.validated_data["qr_data"]

        try:
            data_parts = dict(part.split(":") for part in qr_data.split(","))
            attendee_id = data_parts.get("ID")

            attendee = Attendee.get_attendee_by_id(attendee_id=attendee_id)
            
            attendee.update_status_to_attended()

            return Response({
                "detail": f"{attendee.participant.title} {attendee.participant.last_name} authenticated for {attendee.conference.conference_name}."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"QR Code verification failed: {str(e)}")
            return Response({"detail": "User or Conference not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_description="Mark an abstract as approved",
        operation_summary="Approve abstract",
        method="post",
        tags=["Abstract"],
        request_body=AbstractStatusUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Abstract approved successfully.")
                    }
                ),
            ),
        }
    )
    @action(detail=False, methods=['post'])
    def approve_abstract(self, request: HttpRequest):
        """Mark an abstract as approved."""
        user = cast(User, request.user)

        if not request.user.is_authenticated and user.role not in [ROLE.ORGANIZER.value, ROLE.ADMIN.value]:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = AbstractStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            with transaction.atomic():
                abstract = Abstract.mark_as_approved(validated_data.get('abstract_id'))

                if not abstract:
                    return Response({"detail": "Abstract not found or already processed"}, status=status.HTTP_404_NOT_FOUND)
                
                return Response(data={"detail": "Abstract approved successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Reject an abstract with an optional comment",
        operation_summary="Reject an Abstract",
        method="post",
        tags=["Abstract"],
        request_body=AbstractStatusUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Successfully abstract rejected",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Abstract rejected successfully"),
                    }
                ),
            )
        }
    )
    @action(detail=False, methods=['post'])
    def reject(self, request: HttpRequest):
        """Reject an abstract with an optional comment."""
        user = cast(User, request.user)

        if not request.user.is_authenticated and user.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = AbstractStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    abstract = Abstract.mark_as_rejected(serializer.validated_data['abstract_id'], serializer.validated_data.get('comment'))
                    
                    if abstract:
                        send_rejection_email(user=abstract.user, comment=serializer.validated_data.get('comment'))
                        return Response(data={"detail": "Abstract rejected successfully"}, status=status.HTTP_200_OK)
                    return Response({"detail": "Abstract not found or already processed"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Retrieve abstracts filtered by status for the organizer",
        operation_summary="Retrieve Abstracts by Status",
        method="get",
        tags=["Abstract"],
        responses={
            200: openapi.Response(
                description="Successfully retrieved",
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
                                    'abstract_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'sub_theme': openapi.Schema(type=openapi.TYPE_STRING),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'authors': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'keywords': openapi.Schema(type=openapi.TYPE_STRING),
                                    'document': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'sent_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time", nullable=True),
                                    'comment': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'is_payment_done': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'user': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                                            'affiliation': openapi.Schema(type=openapi.TYPE_STRING),
                                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                                            'country': openapi.Schema(type=openapi.TYPE_STRING),
                                            'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                                            'invitation_status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                            'invitation_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                        }
                                    )
                                }
                            )
                        ),
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
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred while retrieving the abstract")
                    }
                ),
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'conference_id',
                openapi.IN_QUERY,
                description="Conference ID",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Abstract status to filter (e.g., Approved, Pending, All)",
                type=openapi.TYPE_STRING,
                enum=AbstractStatus.values() + ['All'],
            ),
            openapi.Parameter(
                'search_query',
                openapi.IN_QUERY,
                description="Search query for filtering abstracts by user name",
                type=openapi.TYPE_STRING,
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def filtered_abstracts(self, request: HttpRequest):
        user = cast(User, request.user)

        if not user.is_authenticated and user.role != ROLE.ORGANIZER.value:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        conference_id = request.GET.get("conference_id")
        search_query = request.GET.get("search_query")
        status_param = request.GET.get("status") 
        
        if not conference_id:
            return Response(
                {"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            if conference is None:
                return Response({"detail": "Conference not found."}, status=status.HTTP_404_NOT_FOUND)

            main_theme = MainTheme.get_theme_by_conference(conference=conference)
            if main_theme is None:
                return Response({"detail": "Conference has no main theme"}, status=status.HTTP_400_BAD_REQUEST)

            abstracts = Abstract.get_abstracts_by_status(
                main_theme=main_theme,
                status=status_param,
                search_query=search_query
            )

            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(abstracts, request)

            if page is not None:
                serializer = AbstractSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = AbstractSerializer(abstracts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error while retrieving abstracts for user {user.user_id}: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
            
    @swagger_auto_schema(
        operation_description="Retrieve all conference abstracts for the organizer",
        operation_summary="Retrieve Conference Abstracts",
        method="get",
        tags=["Abstract"],
        responses={
            200: openapi.Response(
                description="Successfully retrieved",
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
                                    'abstract_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'sub_theme': openapi.Schema(type=openapi.TYPE_STRING),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'authors': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'keywords': openapi.Schema(type=openapi.TYPE_STRING),
                                    'document': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'sent_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time", nullable=True),
                                    'comment': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'is_payment_done': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'user': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                                            'affiliation': openapi.Schema(type=openapi.TYPE_STRING),
                                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                                            'country': openapi.Schema(type=openapi.TYPE_STRING),
                                            'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                                            'invitation_status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                            'invitation_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                        }
                                    )
                                }
                            )
                        ),
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
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred while retrieving the abstract")
                    }
                ),
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'conference_id',
                openapi.IN_QUERY,
                description="Conference ID",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'search_query', openapi.IN_QUERY,
                description="Search query for filtering abstracts",
                type=openapi.TYPE_STRING,
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def conference_abstracts(self, request: HttpRequest):
        user = cast(User, request.user)

        if not user.is_authenticated and user.role != ROLE.ORGANIZER.value:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        conference_id = request.GET.get("conference_id")
        search_query = request.GET.get("search_query")
        
        
        if not conference_id:
            return Response(
                data={"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            
            if conference is None:
                return Response(data={"detail": "Conference not found."}, status=status.HTTP_404_NOT_FOUND)
            
            main_theme = MainTheme.get_theme_by_conference(conference=conference)
            
            if main_theme is None:
                return Response(data={"detail": "Conference have no main theme"}, status=status.HTTP_400_BAD_REQUEST)
            
            abstracts = Abstract.get_conference_abstracts(main_theme=main_theme, search_query=search_query)
            
            
            
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(abstracts, request)
            
            if page is not None:
                response_serializer = AbstractSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)
            
            response_serializer = AbstractSerializer(abstracts, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error while retrieving abstracts {user.user_id}: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
