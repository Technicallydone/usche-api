# invitation/views.py

import logging
from typing import cast

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from invitation.models import Invitation
from invitation.serializers import (
    InvitationUserResponseSerializer,
    SendInvitationSerializer,
    InvitationFilterQuerySerializer
)
from conference.models import Conference
from user.models import User
from user.permissions import HasAppPermission
from user.enums.permission_enums import AppPermissionEnum
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)


class InvitationViewSet(viewsets.ViewSet):
    """
    ViewSet for managing conference invitations.
    """

    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        "send_invitations": AppPermissionEnum.SEND_INVITATION.value,
        "list": AppPermissionEnum.READ_INVITATION.value,
    }
    
    def list(self, request: Request):
        serializer = InvitationFilterQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            users = User.filter_users_for_invitation(
                conference_id=serializer.validated_data.get("conference_id"),
                search_query=serializer.validated_data.get("search_query"),
                invitation_status=serializer.validated_data.get("invitation_status"),
                created_from=serializer.validated_data.get("created_from"),
                created_to=serializer.validated_data.get("created_to"),
            )

            paginator = PageNumberPagination()
            paginator.page_size_query_param = "page_size"

            page = paginator.paginate_queryset(users, request)

            response_serializer = InvitationUserResponseSerializer(
                page if page is not None else users,
                many=True,
            )

            if page is not None:
                return paginator.get_paginated_response(
                    response_serializer.data
                )

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Error fetching invitation users: {e}",
                exc_info=True,
            )
            return Response(
                {"detail": "An error occurred while fetching invitation users"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="send")
    def send_invitations(self, request: Request):
        serializer = SendInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                conference_id = serializer.validated_data.get("conference_id")

                users_ids = list(
                    set(serializer.validated_data.get("users_ids") or [])
                )

                conference = Conference.get_conference_by_id(
                    conference_id=conference_id
                )

                if not conference:
                    return Response(
                        {"detail": "Conference not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if conference.is_conference_outdated():
                    return Response(
                        {
                            "detail": "The conference has already ended. Invitations are not allowed."
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                users = User.get_users_by_ids(user_ids=users_ids)

                if not users.exists():
                    return Response(
                        {"detail": "No valid users found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                existing_user_ids = set(
                    Invitation.objects.filter(
                        conference=conference,
                        user_id__in=users_ids,
                    ).values_list("user_id", flat=True)
                )

                users_to_invite = [
                    user for user in users
                    if user.user_id not in existing_user_ids
                ]

                if not users_to_invite:
                    return Response(
                        {"detail": "All selected users have already been invited."},
                        status=status.HTTP_200_OK,
                    )

                unique_users_to_invite = {
                    user.user_id: user for user in users_to_invite
                }.values()

                invitations = Invitation.add_users(
                    users=list(unique_users_to_invite),
                    conference=conference,
                )

            logger.info(
                f"{len(invitations)} invitations created for conference {conference_id}"
            )

            return Response(
                {
                    "detail": f"Successfully sent invitations to {len(invitations)} users.",
                    "skipped": len(users_ids) - len(users_to_invite),
                    "deduplicated_input": len(set(serializer.validated_data.get("users_ids") or [])),
                },
                status=status.HTTP_200_OK,
            )

        except ObjectDoesNotExist:
            logger.error("Conference or users not found during invitation process")
            return Response(
                {"detail": "Conference or users not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error sending invitations: {e}", exc_info=True)
            return Response(
                {"detail": "An error occurred while sending invitations"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )