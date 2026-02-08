import logging
from typing import cast
from django.http import HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from attendee.models import Attendee
from attendee.serializers import AttendeeResponseSerializer
from conference.models import Conference
from django.core.exceptions import ValidationError
from user.models import User
from rest_framework.pagination import PageNumberPagination

import base64

from utils.qr_code_generator import generate_qr_code


logger = logging.getLogger(__name__)

class AttendeeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def conference_attendees(self, request: HttpRequest): 
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
