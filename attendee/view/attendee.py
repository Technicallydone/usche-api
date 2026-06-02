import base64
import logging
from typing import cast

from django.core.exceptions import ValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from attendee.enums.attendee_status import AttendeeStatus
from attendee.models import Attendee
from attendee.serializers import (
    AttendeeSerializer,
    UpdateAttendeeStatusSerializer,
)
from conference.models import Conference
from user.enums.permission_enums import AppPermissionEnum
from user.models import User
from user.permissions import HasAppPermission
from user.serializers import UserFilterQuerySerializer
from utils.qr_code_generator import generate_qr_code

logger = logging.getLogger(__name__)


class AttendeeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        "list": AppPermissionEnum.READ_ATTENDEES.value,
        "retrieve": AppPermissionEnum.READ_ATTENDEES.value,
        "update_status": AppPermissionEnum.UPDATE_ATTENDEE_STATUS.value,
        "ticket_request": AppPermissionEnum.REQUEST_JOIN_TICKET.value,
        "verify-attendee": AppPermissionEnum.VERIFY_ATTENDEE.value,
    }
    
    @action(
        detail=False,
        methods=["get"],
        url_path="verify-attendee"
    )
    def verify_attendee(self, request: Request):
        user_id = request.query_params.get("user_id")
        conference_id = request.query_params.get("conference_id")

        if not user_id:
            return Response(
                {"detail": "User ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not conference_id:
            return Response(
                {"detail": "Conference ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            conference = Conference.objects.filter(
                conference_id=conference_id
            ).first()

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            attendee = (
                Attendee.objects
                .select_related(
                    "participant",
                    "conference",
                )
                .filter(
                    participant_id=user_id,
                    conference_id=conference_id,
                )
                .first()
            )

            if not attendee:
                return Response(
                    {"detail": "Attendee not found for this conference"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if attendee.status == AttendeeStatus.ATTENDED.value:
                return Response(
                    {
                        "detail": "Attendee already checked in",
                        "attendee": AttendeeSerializer(attendee).data,
                    },
                    status=status.HTTP_200_OK,
                )

            attendee.status = AttendeeStatus.ATTENDED.value
            attendee.save(update_fields=["status"])

            return Response(
                {
                    "detail": "Attendee verified successfully",
                    "attendee": AttendeeSerializer(attendee).data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Verify attendee error: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------
    # LIST ATTENDEES
    # -----------------------------------
    def list(self, request: Request):
        serializer = UserFilterQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        search_query = serializer.validated_data.get("search_query")
        created_from = serializer.validated_data.get("created_from")
        created_to = serializer.validated_data.get("created_to")
        conference_id = serializer.validated_data.get("conference_id")
        invitation_status = serializer.validated_data.get("invitation_status")
        attendee_status = serializer.validated_data.get("status")

        try:
            attendees = Attendee.filter_attendees(
                search_query=search_query,
                created_from=created_from,
                created_to=created_to,
                conference_id=conference_id,
                invitation_status=invitation_status,
                attendee_status=attendee_status
            )

            paginator = PageNumberPagination()
            paginator.page_size_query_param = "page_size"

            page = paginator.paginate_queryset(attendees, request)

            serializer = AttendeeSerializer(
                page if page is not None else attendees,
                many=True,
            )

            if page is not None:
                return paginator.get_paginated_response(serializer.data)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching attendees: {e}", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------
    # RETRIEVE ATTENDEE
    # -----------------------------------
    def retrieve(self, request: Request, pk=None):
        try:
            attendee = (
                Attendee.objects.select_related("participant", "conference")
                .filter(attendee_id=pk)
                .first()
            )

            if not attendee:
                return Response(
                    {"detail": "Attendee not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                AttendeeSerializer(attendee).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Retrieve error {pk}: {e}", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------
    # UPDATE STATUS
    # -----------------------------------
    @action(detail=True, methods=["patch"], url_path="update-status")
    def update_status(self, request: Request, pk=None):
        serializer = UpdateAttendeeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            attendee = Attendee.objects.filter(attendee_id=pk).first()

            if not attendee:
                return Response(
                    {"detail": "Attendee not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            attendee.status = serializer.validated_data["status"]
            attendee.save(update_fields=["status"])

            return Response(
                {
                    "detail": "Status updated successfully",
                    "attendee": AttendeeSerializer(attendee).data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Status update error {pk}: {e}", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------
    # REQUEST TICKET
    # -----------------------------------
    @action(detail=False, methods=["get"], url_path="ticket/request")
    def ticket_request(self, request: Request):
        user = cast(User, request.user)
        conference_id = request.query_params.get("conference_id")

        if not conference_id:
            return Response(
                {"detail": "Conference id not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            conference = Conference.get_conference_by_id(conference_id)

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if conference.is_conference_outdated():
                return Response(
                    {"detail": "Conference already ended"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            attendee = Attendee.get_attendee(
                participant=user,
                conference=conference,
            )

            if not attendee:
                return Response(
                    {
                        "detail": "You are not registered as an attendee"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            qr_data = f"ID:{attendee.attendee_id},U:sche"
            qr_image = generate_qr_code(qr_data)

            qr_base64 = base64.b64encode(qr_image.read()).decode("utf-8")

            return Response(
                {
                    "detail": "Ticket generated successfully",
                    "qr_code_base64": qr_base64,
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Ticket error {user}: {e}", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )