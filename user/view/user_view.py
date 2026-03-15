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
from services.email.tasks import send_email_task
from usche_app import settings
from user.enums.permission_enums import AppPermissionEnum
from user.models import User
from user.permissions import HasAppPermission
from user.serializer.query_serializer import UserFilterQuerySerializer
from user.serializers import (
    UserResponseSerializer,
    UserResponseSerializer,
    ChangePasswordRequestSerializer
)
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    MAX_FAILED_ATTEMPTS = 5
    LOCK_DURATION_MINUTES = 15
    
    permission_classes = [IsAuthenticated, HasAppPermission]
    
    permission_mapping = {
        'list': AppPermissionEnum.VIEW_USERS,
        'users_report': AppPermissionEnum.VIEW_USERS_REPORT.value,
        'change_password': AppPermissionEnum.CHANGE_PASSWORD.value
    }
    
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