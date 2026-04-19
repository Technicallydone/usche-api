import logging
from typing import cast
from django.http import HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from abstracts.models import Abstract
from abstracts.serializers import AbstractSerializer
from conference.models import Conference
from themes.models import MainTheme
from user.models import User

logger = logging.getLogger(__name__)

class AbstractReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def conference_abstract_report(self, request: HttpRequest):
        user = cast(User, request.user)

        conference_id = request.GET.get("conference_id")
        abstract_status = request.GET.get("abstract_status")

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
                return Response(data={"detail": "Conference has no main theme"}, status=status.HTTP_400_BAD_REQUEST)

            abstract_report = Abstract.conference_abstract_report(main_theme=main_theme, abstract_status=abstract_status)
            response_serializer = AbstractSerializer(abstract_report, many=True)

            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error while retrieving paid abstracts for user {user.user_id}: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
