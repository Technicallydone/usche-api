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
from conference.models import Conference
from user.enums.role import ROLE
from user.models import User

logger = logging.getLogger(__name__)

class AttendeeReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        method='get',
        operation_summary="Conference Attendee Report",
        operation_description="Retrieve a list of attendees report for a specific conference.",
        tags=["Attendee"],
        manual_parameters=[
            openapi.Parameter(
                name='conference_id',
                in_=openapi.IN_QUERY,
                description='ID of the conference',
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Attendees retrieved successfully",
                schema=openapi.Schema(
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
    def conference_attendees_report(self, request: HttpRequest): 
        user = cast(User, request.user)

        if not request.user.is_authenticated or user.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
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
            
        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            
            if conference is None:
                return Response(data={"detail": "Conference not found."}, status=status.HTTP_404_NOT_FOUND)
            
            attendees = Attendee.conference_attendee_report(conference=conference)
            response_serializer = AttendeeResponseSerializer(attendees, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error while retrieving conference attendees", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
