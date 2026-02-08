import logging
from typing import cast
from django.http import HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from attendee.models import Attendee
from attendee.serializers import AttendeeResponseSerializer
from conference.models import Conference
from user.models import User

logger = logging.getLogger(__name__)

class AttendeeReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def conference_attendees_report(self, request: HttpRequest): 
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
