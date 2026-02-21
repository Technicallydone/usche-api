# invitation/views.py
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.http import HttpRequest
from django.core.exceptions import ObjectDoesNotExist
from invitation.models import Invitation
from invitation.serializers import InvitationUserSerializer, SendInvitationSerializer
from conference.models import Conference

from user.enums.invitation_status import InvitationStatusEnum
from user.models import User

logger = logging.getLogger(__name__)

class InvitationViewSet(viewsets.ModelViewSet):
    """
    A viewset for listing, filtering, and retrieving invitations.
    """
    def get_serializer_class(self):
        return InvitationUserSerializer
    
    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated] 
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return None  
    
    @action(detail=False, methods=['post'])
    def send_invitations(self, request: HttpRequest):
        """Add users to queue for sending invitations"""
        request_serializer = SendInvitationSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        users_ids = request_serializer.validated_data.get("users_ids")

        try:
            conference = Conference.get_conference_by_id(conference_id=request_serializer.validated_data.get("conference_id"))
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            if conference.is_conference_outdated():
                return Response(data={"detail": "The conference has already ended, you are not allowed to invite people."}, status=status.HTTP_403_FORBIDDEN)
            
            users = User.get_users_by_ids(user_ids=users_ids)

            if not users.exists():
                return Response(
                    data={"detail": "No valid attendees found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            invitations = Invitation.add_users(users=users, conference=conference)

            return Response(
                data={"detail": f"Invitations sent to {len(invitations)} attendees"},
                status=status.HTTP_200_OK
            )
        
        except ObjectDoesNotExist:
            logger.error("Error: Conference or Users not found")
            return Response(
                data={"detail": "Conference or Users not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.error(f"Error while sending invitations: {e}")
            return Response(
                data={"detail": "An error occurred while adding users to the queue"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def invitation_list(self, request: HttpRequest):
        """
        List all users with their invitation status for a specific conference.

        Possible filter types:
        - 'all': all users with invitation status
        - 'invited': only users who are invited
        - 'not_invited': only users who are not invited
        - 'invited_not_sent': only users who are invited but the invitation is not sent
        """
        if not request.user.is_authenticated:
            return Response(
                data={"detail": "You are not authorized to view invitations."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        conference_id = request.GET.get("conference_id")
        if not conference_id:
            return Response(
                data={"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conference = Conference.objects.get(conference_id=conference_id)
        except Conference.DoesNotExist:
            return Response(
                data={"detail": "Conference not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        filter_type = request.GET.get("filter_type", InvitationStatusEnum.ALL.value)

        search_query = request.GET.get("search_query")

        try:
            users_with_invitation_status = Invitation.filter_users(
                conference=conference,
                filter_type=filter_type,
                search_query=search_query
            )
            
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(users_with_invitation_status, request)
            
            if page is not None:
                response_serializer = InvitationUserSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)
            
            response_serializer = InvitationUserSerializer(users_with_invitation_status, many=True)
            return Response(data=response_serializer.data, status=status.HTTP_200_OK)
        
        except ValueError as e:
            logger.error(f"Value error while retrieving invitation users: {e}", exc_info=True)
            return Response(data={"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error occurred while listing invitations: {e}")
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
