from typing import cast
from django.http import HttpRequest
from rest_framework import viewsets, status, permissions
import logging
from rest_framework.response import Response
from django.db import transaction
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.enums.invitation_status import InvitationStatusEnum
from user.models import User
from user.serializers import RequestRegistration, UsersSerializer, UserResponseSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from conference.models import Conference

from user.tasks import process_registration

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        return RequestRegistration
    
    def get_permissions(self):
        if self.action == 'request_registration':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.AllowAny]
            
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        return None
    
    @swagger_auto_schema(
        operation_description="Request registration by providing necessary information. eg,. first name, last name and contact info.",
        operation_summary="Request Registration",
        method="post",
        tags=["User"],
        responses={
            201: openapi.Response(
                description="Data saved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        }
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        
        serializer = RequestRegistration(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        try:
            conference = Conference.get_latest_conference()
            
            if not conference.registration_open:
                logger.warning("403: Registration is closed for the current conference.")
                return Response(
                    data={"detail": "Registration closed. For any inquiries, please contact info@usche.ac.tz or call +255 700 123 456."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            process_registration.delay(validated_data)
            
            return Response(
                data={"detail": "You have successfully registered. A confirmation email has been sent to you for activation."},
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as ve:
            logger.error(f"Validation error: {str(ve)}", exc_info=True)
            return Response(
                data={"detail": f"Validation error: {str(ve)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"Error occurred during registration: {str(e)}", exc_info=True)
            return Response(
                data={"detail": "An internal server error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @swagger_auto_schema(
        operation_description="Retrieve Users",
        operation_summary="Retrieve all users",
        method="get",
        tags=["User"],
        responses={
            200: openapi.Response(
                description="Successfully retrieved list of users",
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
                                    'first_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'last_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'phone_number': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'country': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'occupation': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                                    'invitation_status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'invitation_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'affiliation': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                }
                            )
                        ),
                    }
                ),
            ),
            400: openapi.Response(
                description="Bad Request - Missing or invalid parameters"
            ),
            404: openapi.Response(
                description="Not Found - Conference not found"
            ),
            500: openapi.Response(
                description="Internal Server Error"
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'search_query', openapi.IN_QUERY,
                description="Search query for filtering users",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'is_active', openapi.IN_QUERY,
                description="Filter users by active status: true, false, or leave empty for all",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'conference_id', openapi.IN_QUERY,
                description="ID of the conference",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'filter_type', openapi.IN_QUERY,
                description="Filter invitations by status",
                type=openapi.TYPE_STRING,
                enum=[status.value for status in InvitationStatusEnum]
            ),
        ]
    )
    @action(detail=False, methods=["get"])
    def users(self, request: HttpRequest):
        user = request.user

        if not user.is_authenticated:
            return Response(
                data={"detail": "You are not authorized to view this resource"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        search_query = request.GET.get("search_query")
        is_active = request.GET.get("is_active") == "true"
        conference_id = request.GET.get("conference_id")
        filter_type = request.GET.get("filter_type", InvitationStatusEnum.ALL.value)

        search_query = request.GET.get("search_query")
        
        if not conference_id:
            return Response(
                data={"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            
            if not conference:
                return Response(data={"detail": "No conference found"}, status=status.HTTP_404_NOT_FOUND)
            
            users = User.users(
                conference=conference,
                filter_type=filter_type,
                search_query=search_query,
                is_active=is_active
            )

            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(users, request)
            
            if page is not None:
                response_serializer = UsersSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)
            
            response_serializer = UsersSerializer(users, many=True)
            return Response(data=response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving all users: {e}")
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @swagger_auto_schema(
        operation_description="List of all users (no pagination, with active status filter)",
        operation_summary="All users (non-paginated, filterable)",
        method="get",
        tags=["User"],
        responses={
            200: openapi.Response(
                description="Users retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'country': openapi.Schema(type=openapi.TYPE_STRING),
                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                            'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
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
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred while retrieving users")
                    }
                ),
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'search_query', openapi.IN_QUERY,
                description="Search query for filtering users",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'is_active', openapi.IN_QUERY,
                description="Filter users by active status: true, false, or leave empty for all",
                type=openapi.TYPE_BOOLEAN
            )
        ]
    )
    @action(detail=False, methods=["get"], url_path="user-report")
    def users_report(self, request: HttpRequest):
        user = request.user

        if not user.is_authenticated:
            return Response(
                data={"detail": "You are not authorized to view this resource"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        search_query = request.GET.get("search_query")
        is_active_param = request.GET.get("is_active")

        try:
            users = User.user_report(search_query=search_query)

            if is_active_param is not None:
                if is_active_param.lower() == 'true':
                    users = users.filter(is_active=True)
                elif is_active_param.lower() == 'false':
                    users = users.filter(is_active=False)

            serializer = UserResponseSerializer(users, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving all users: {e}")
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )