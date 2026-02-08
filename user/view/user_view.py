from rest_framework import viewsets, status
from rest_framework.request import Request
import logging
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from user.enums.invitation_status import InvitationStatusEnum
from user.enums.permission_enums import AppPermissionEnum
from user.enums.user_role_action_enum import UserRoleActionEnum
from user.models import User
from user.permissions import HasAppPermission
from user.serializer.query_serializer import UserFilterQuerySerializer
from user.serializers import (
    UserResponseSerializer,
    UserResponseSerializer,
    UserRoleAssignmentSerializer,
    UserProfileSerializer
)
from rest_framework.pagination import PageNumberPagination
from conference.models import Conference

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ViewSet):
    
    permission_classes = [IsAuthenticated, HasAppPermission]
    
    permission_mapping = {
        "list": AppPermissionEnum.VIEW_USERS.value,
        "assign_role": AppPermissionEnum.CHANGE_USER_ROLE.value,
        "users_report": AppPermissionEnum.VIEW_USERS_REPORT.value,
        "retrieve": AppPermissionEnum.VIEW_PROFILE.value,
    }
    
    def retrieve(self, request: Request, pk=None):
        """
        Retrieve a single user by ID.
        URL: GET /api/v1/accounts/users/{user_id}/
        """
        if pk is None:
            return Response(
                {"detail": "User ID is required in the URL."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.filter(user_id=pk).first()
            if not user:
                raise NotFound(detail=f"User with ID {pk} not found.")

            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except NotFound as e:
            return Response({"detail": e.detail}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request: Request):
        """
        Retrieve the profile of the currently authenticated user.
        URL: GET /api/v1/accounts/users/me/
        """
        try:
            user = request.user
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=["post"], url_path="role")
    def assign_role(self, request: Request, pk=None):
        """
        Assign or unassign a role to a user.
        URL: POST /api/v1/accounts/users/{user_id}/role/
        Payload:
        {
            "role_id": "<uuid>",
            "action": "assign" | "unassign"
        }
        """
        if pk is None:
            return Response(
                {"detail": "User ID is required in the URL."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserRoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        role_id = validated_data.get("role_id")
        action_str = validated_data.get("action")

        try:
            action_enum = UserRoleActionEnum(action_str)
        except ValueError:
            return Response(
                {"detail": "Invalid action. Must be 'assign' or 'unassign'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            User.change_role(
                user_id=pk,
                role_id=role_id,
                action=action_enum
            )
             
            return Response(data={"detail": f"Role successfully {action_enum.value}ed."}, status=status.HTTP_200_OK)
            
        except NotFound as e:
            return Response(data={"detail": e.detail}, status=status.HTTP_404_NOT_FOUND)
        
        except ValidationError as e:
            return Response(data=e.error_dict, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    
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