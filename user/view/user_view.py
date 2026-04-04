from datetime import timedelta
from django.utils import timezone
from typing import cast

from rest_framework import viewsets, status
from rest_framework.request import Request
import logging
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from django.contrib.auth import authenticate
from authentication import serializer
from services.email.tasks import send_email_task
from usche_app import settings
from user.enums.permission_enums import AppPermissionEnum
from user.models import Role
from user.models import User
from user.permissions import HasAppPermission
from user.serializers import (
    UserResponseSerializer,
    UserResponseSerializer,
    ChangePasswordRequestSerializer,
    UserProfileSerializer,
    UserRoleAssignmentSerializer,
    UserFilterQuerySerializer
)
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    MAX_FAILED_ATTEMPTS = 5
    LOCK_DURATION_MINUTES = 15
    
    permission_classes = [IsAuthenticated, HasAppPermission]
    
    permission_mapping = {
        'list': AppPermissionEnum.READ_USERS.value,
        'users_report': AppPermissionEnum.READ_USERS_REPORT.value,
        'change_password': AppPermissionEnum.CHANGE_PASSWORD.value,
        'get_profile': AppPermissionEnum.READ_PROFILE.value,
        'retrieve_user': AppPermissionEnum.READ_USERS.value,
        'toggle_staff': AppPermissionEnum.UPDATE_STAFF_STATUS.value,
        'toggle_active': AppPermissionEnum.MANAGE_STAFF_MEMBERSHIP.value,
    }
    
    @action(detail=True, methods=['patch'], url_path='change-role')
    def change_role(self, request: Request, pk=None):
        """
        Change the role of a user.
        """
        # Validate request data with serializer
        serializer = UserRoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role_id = serializer.validated_data.get("role_id")
        
        if not pk:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            user = User.get_user_by_id(user_id=pk)
            if not user:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            role = Role.find_by_id(role_id)
            if not role:
                return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

            user.role = role
            user.save(update_fields=["role"])

            return Response(
                {"detail": f"User role updated to '{role.name}'"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception(f"Error changing role for user {pk}: {str(e)}")
            return Response(
                {"detail": "An error occurred while changing user role."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='detail')
    def retrieve_user(self, request: Request, pk=None):
        if not pk:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user = User.get_user_by_id(user_id=pk)

        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='toggle-staff')
    def toggle_staff(self, request, pk=None):
        """
        Toggle the is_staff status of a user.
        """
        try:
            if not pk:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            user = User.get_user_by_id(user_id=pk)
            if not user:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            user.is_staff = not user.is_staff
            user.save(update_fields=["is_staff"])

            return Response(
                {"detail": f"is_staff set to {user.is_staff}"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.exception(f"Error toggling is_staff for user {pk}: {str(e)}")
            return Response(
                {"detail": "An error occurred while toggling is_staff."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """
        Toggle the is_active status of a user.
        """
        try:
            if not pk:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            user = User.get_user_by_id(user_id=pk)
            if not user:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            user.is_active = not user.is_active
            user.save(update_fields=["is_active"])

            return Response(
                {"detail": f"is_active set to {user.is_active}"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.exception(f"Error toggling is_active for user {pk}: {str(e)}")
            return Response(
                {"detail": "An error occurred while toggling is_active."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='me')
    def get_profile(self, request: Request):
        try:
            user = cast(User, request.user)
            serializer = UserProfileSerializer(user)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(data=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['patch'], url_path='change-password')
    def change_password(self, request: Request):
        serializer = ChangePasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            user = cast(User, request.user)
            logger.info(f'Validating user {user.email} for password change')

            # Check if account is locked
            if user.locked_until and user.locked_until > timezone.now():
                remaining = (user.locked_until - timezone.now()).seconds // 60
                raise PermissionDenied(
                    f"Account locked due to multiple failed attempts. Try again in {remaining} minutes."
                )

            # Verify current password
            authenticated_user = authenticate(email=user.email, password=validated_data.get('current_password'))

            if not authenticated_user:
                # Increment failed attempts
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                    # Lock the account
                    user.locked_until = timezone.now() + timedelta(minutes=self.LOCK_DURATION_MINUTES)
                    user.failed_login_attempts = 0
                    user.save(update_fields=["failed_login_attempts", "locked_until"])

                    # Send account lock email
                    send_email_task.delay(
                        subject="Your Account Has Been Locked",
                        to=user.email,
                        greeting=f"Hello {user.first_name},",
                        lines=[
                            f"Your account has been temporarily locked due to {self.MAX_FAILED_ATTEMPTS} failed password attempts.",
                            f"You can try again in {self.LOCK_DURATION_MINUTES} minutes.",
                            "If this was not you, please contact support immediately."
                        ],
                        salutations=["Best regards,", "The USChE Team"],
                        button_text="Login to Your Account",
                        button_url=f"{settings.FRONTEND_BASE_URL}/auth",
                        footer_text="© 2026 USChE - University of Dodoma"
                    )

                else:
                    user.save(update_fields=["failed_login_attempts"])
                raise AuthenticationFailed("Invalid current password")

            user.failed_login_attempts = 0
            user.locked_until = None
            user.set_password(validated_data.get('new_password'))
            user.save(update_fields=['password', 'failed_login_attempts', 'locked_until'])

            send_email_task.delay(
                subject="Your Password Has Been Changed",
                to=user.email,
                greeting=f"Hello {user.first_name},",
                lines=[
                    "Your account password has been successfully changed.",
                    "If you did not initiate this change, please reset your password immediately or contact support."
                ],
                salutations=["Best regards,", "The USChE Team"],
                button_text="Login to Your Account",
                button_url=f"{settings.FRONTEND_BASE_URL}/auth",
                footer_text="© 2026 USChE - University of Dodoma"
            )

            return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)

        except AuthenticationFailed as e:
            logger.warning(f"Authentication failed for {user.email}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except PermissionDenied as e:
            logger.warning(f"Permission denied for {user.email}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.exception(f"Unexpected error for {user.email}: {str(e)}")
            return Response({"detail": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def list(self, request: Request):
        serializer = UserFilterQuerySerializer(data=request.query_params)
        
        serializer.is_valid(raise_exception=True)

        search_query = serializer.validated_data.get("search_query")
        staff = serializer.validated_data.get("staff")
        created_from = serializer.validated_data.get("created_from")
        created_to = serializer.validated_data.get("created_to")

        try:
            users = User.filter_users(
                search_query=search_query,
                staff=staff,
                created_from=created_from,
                created_to=created_to
            )

            paginator = PageNumberPagination()
            paginator.page_size_query_param = 'page_size'
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