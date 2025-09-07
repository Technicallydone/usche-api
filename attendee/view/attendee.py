import logging
from typing import cast
from django.http import HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import action
from attendee.models import Attendee
from attendee.serializers import AttendeeResponseSerializer
from attendee.tasks import process_issue_ticket
from conference.models import Conference
from django.core.exceptions import ValidationError
from user.enums.role import ROLE
from user.models import User
from rest_framework.pagination import PageNumberPagination

import base64

from utils.qr_code_generator import generate_qr_code


logger = logging.getLogger(__name__)

class AttendeeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Get conference attendees",
        operation_description="Retrieve a paginated list of attendees for a specific conference.",
        tags=["Attendee"],
        manual_parameters=[
            openapi.Parameter(
                name='conference_id',
                in_=openapi.IN_QUERY,
                description='ID of the conference',
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'search_query', openapi.IN_QUERY,
                description="Search query for filtering abstracts",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={
            200: openapi.Response(
                description="Attendees retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'attendee_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'conference': openapi.Schema(type=openapi.TYPE_STRING),
                                    'participant': openapi.Schema(type=openapi.TYPE_STRING),
                                    'invitation_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'participant': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                                            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'email': openapi.Schema(type=openapi.TYPE_STRING, format="email"),
                                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                            'country': openapi.Schema(type=openapi.TYPE_STRING),
                                            'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request - Missing or invalid conference ID",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Conference ID is required.")
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized - User is not an organizer",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="You are not authorized to perform this task")
                    }
                )
            ),
            404: openapi.Response(
                description="Conference not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Conference not found.")
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def conference_attendees(self, request: HttpRequest): 
        user = cast(User, request.user)

        if not request.user.is_authenticated and user.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
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
            
            attendees = Attendee.get_conference_attendees(conference=conference, search_query=search_query)
            
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(attendees, request)
            
            if page is not None:
                response_serializer = AttendeeResponseSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)
            
            response_serializer = AttendeeResponseSerializer(attendees, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error while retrieving conference attendees", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Request ticket for the authenticated attendee",
        operation_summary="Issue ticket",
        method="get",
        tags=["Attendee"],
        responses={
            200: openapi.Response(
                description="Ticket successfully generated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Ticket successfully generated."
                        ),
                        "qr_code_base64": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="iVBORw0KGgoAAAANSUhEUgAA...",
                            description="Base64 encoded QR code image for the ticket"
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request - Invalid conference or not provided | Attendee not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Conference id not provided | We were unable to verify your attendance. If you believe this is an error, please contact our support team for assistance.")
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
            403: openapi.Response(
                description="Forbidden - Conference for the requested ticked has already ended",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="We regret to inform you that the conference has already ended.")
                    }
                ),
            ),
            404: openapi.Response(
                description="Not Found - Conference for the provided ID not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Conference not found")
                    }
                ),
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred while sending invitations")
                    }
                ),
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'conference_id', openapi.IN_QUERY,
                description="Conference ID for specific attendees to the conference",
                type=openapi.TYPE_STRING,
            )
        ]
    )
    @action(detail=False, methods=["get"])
    def request_ticket(self, request: HttpRequest):
        if not request.user.is_authenticated:
            return Response(data={"detail": "You are not authorized to request ticket for this conference"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = cast(User, request.user)
        conference_id = request.GET.get('conference_id')
        
        if conference_id is None:
            return Response(data={"detail": "Conference id not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            if conference.is_conference_outdated():
                return Response(data={"detail": "We regret to inform you that the conference has already ended."}, status=status.HTTP_403_FORBIDDEN)
            
            attendee = Attendee.get_attendee(participant=user, conference=conference)
            
            if attendee is None:
                return Response(
                    data={
                        "detail": "We were unable to verify your attendance. If you believe this is an error, please contact our support team for assistance."
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # process_issue_ticket.delay(attendee.attendee_id)
            
            qr_data = f"ID:{attendee.attendee_id},U:sche"
            qr_image = generate_qr_code(qr_data)
            
            qr_base64 = base64.b64encode(qr_image.read()).decode('utf-8')
            
            
            return Response(
                data={
                    "detail": "Ticket successfully generated.",
                    "qr_code_base64": qr_base64
                },
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            logger.error(f"Validation error while issuing ticket for {user}: {e}", exc_info=True)
            return Response(data={"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"An error occured while sending qr code to user - {user}: {e}", exc_info=True)
            return Response(data={"detail": {str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
