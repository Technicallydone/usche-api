import logging
from typing import cast
from django.http import HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import action
from abstracts.enums.abstract_status import AbstractStatus
from abstracts.models import Abstract
from abstracts.serializers import AbstractSerializer
from conference.models import Conference
from theme.models import MainTheme
from user.enums.role import ROLE
from user.models import User

logger = logging.getLogger(__name__)

class AbstractReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all conference abstracts",
        operation_summary="Abstract Report",
        method="get",
        tags=["Abstract"],
        responses={
            200: openapi.Response(
                description="Successfully retrieved",
                schema=openapi.Schema(
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
                            'payment': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'payment_id': openapi.Schema(type=openapi.TYPE_STRING),
                                        'amount': openapi.Schema(type=openapi.TYPE_STRING),
                                        'payment_slip': openapi.Schema(type=openapi.TYPE_STRING),
                                        'comment': openapi.Schema(type=openapi.TYPE_STRING),
                                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                                    }
                                )
                            ),
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
                )
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
                'abstract_status',
                openapi.IN_QUERY,
                description="Status of the abstract. Options: " + ", ".join(AbstractStatus.values()),
                type=openapi.TYPE_STRING,
                enum=AbstractStatus.values(), 
                required=False
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def conference_abstract_report(self, request: HttpRequest):
        user = cast(User, request.user)

        if not request.user.is_authenticated or user.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )

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
