from rest_framework import viewsets, status
from rest_framework.request import Request
import logging
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.enums.invitation_status import InvitationStatusEnum
from user.enums.permission_enums import AppPermissionEnum
from user.enums.user_role_action_enum import UserRoleActionEnum
from user.models import User
from user.permissions import HasAppPermission
from user.serializer.query_serializer import UserFilterQuerySerializer
from user.serializers import (
    UserResponseSerializer,
    UserResponseSerializer,
)
from rest_framework.pagination import PageNumberPagination
from conference.models import Conference

from user.tasks import process_registration

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    
    def get_queryset(self):
        return None
    
    def list(self, request: Request):
        serializer = UserFilterQuerySerializer(data=request.query_params)
        
        serializer.is_valid(raise_exception=True)

        search_query = serializer.validated_data.get("search_query")
        staff = serializer.validated_data.get("staff")
       

        try:
            users = User.search_users(
                search_query=search_query,
                staff=staff
            )

            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(users, request)
            
            if page is not None:
                response_serializer = UserResponseSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)
            
            response_serializer = UserResponseSerializer(users, many=True)
            return Response(data=response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving all users: {e}")
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"], url_path="users/report")
    def users_report(self, request: Request):
        search_query = request.query_params.get("search_query")
        is_active_param = request.query_params.get("is_active")

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