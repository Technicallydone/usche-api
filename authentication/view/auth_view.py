import logging
from typing import cast
from django.core.signing import SignatureExpired
from rest_framework import permissions, status, viewsets
from rest_framework.request import Request
from authentication.serializers import (
    RequestSignInSerializer,
    TokenResponseSerializer,
    SignOutSerializer,
    RequestActivateAccount,
    RequestNewToken,
    RequestChangePasswordSerailizer,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.auth import TokenAuthentication
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from authentication.tasks import process_reset_password_email
from services.email.tasks import send_email_task
from usche_app import settings
from user.model.user_model import User
from utils.access_token import generate_token, verify_token
from django.utils import timezone

logger = logging.getLogger(__name__)

class AuthenticationViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = [
        TokenAuthentication,
        JWTAuthentication,
    ]
    
    @action(detail=False, methods=['post'])
    def change_password(self, request, email = None):
        
        request_serializer = RequestChangePasswordSerailizer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        validated_data = request_serializer.validated_data

        token = validated_data.get("token")
        if not token:
            return Response(
                {"error_code": "MISSING_TOKEN", "detail": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify token and get user_id
            user_id = verify_token(token=token)
            user = User.get_user_by_id(user_id=user_id)

            if user is None:
                return Response(
                    {"error_code": "USER_NOT_FOUND", "detail": "User with given email does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Update password
            user.set_password(raw_password=validated_data.get("new_password"))
            user.save(update_fields=["password"])

            # Send notification email
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

            return Response(
                {"detail": "Password changed successfully. You can now log in with your new password."},
                status=status.HTTP_200_OK
            )

        except ValueError:
            return Response(
                {"error_code": "INVALID_TOKEN", "detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except SignatureExpired as e:
            logger.error(f"Expired token: {e}", exc_info=True)
            return Response(
                {"error_code": "TOKEN_EXPIRED", "detail": "Activation token has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.exception("Error while activating user.", exc_info=e)
            return Response({"error_code": "INTERNAL_SERVER_ERROR", "detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='forgot-password/(?P<email>[^/]+)')
    def forgot_password(self, request, email=None):
        if email is None:
            return Response(data={"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.get_user_by_email(email=email)

            if user is None:
                return Response(data={"detail": "User with given email does not exist"}, status=status.HTTP_404_NOT_FOUND)

            process_reset_password_email.delay(user.user_id)

            return Response(
                data={"detail": "A password reset request has been received. If the email provided is associated with an account, you will receive instructions shortly to reset your password."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error occurred during reset password email: {str(e)}", exc_info=True)
            return Response(
                data={"detail": "An internal server error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=False, methods=['post'], url_path='new-activation-email')
    def new_activation_email(self, request: Request):
        """
        Resend activation email.
        """

        serializer = RequestNewToken(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response(
                    {
                        "error_code": "USER_ALREADY_ACTIVE",
                        "detail": "User is already active."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate fresh activation token
            token = generate_token(user=user)

            # Send activation email asynchronously
            send_email_task.delay(
                subject="Activate Your USChE Account",
                to=user.email,
                greeting=f"Hello {user.first_name},",
                lines=[
                    "You requested a new activation link.",
                    "Please click the button below to activate your account."
                ],
                salutations=["Best regards,", "The USChE Team"],
                button_text="Activate Account",
                button_url=f"{settings.FRONTEND_BASE_URL}/activate/{token}",
                footer_text="© 2026 USChE - University of Dodoma"
            )

            return Response(
                {
                    "detail": "If the account exists and is not activated, a new activation email has been sent."
                },
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {
                    "detail": "If the account exists and is not activated, a new activation email has been sent."
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception("Error while activating user.", exc_info=e)
            return Response({"error_code": "INTERNAL_SERVER_ERROR", "detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def activate_account(self, request):
        """
        Activate the user account by verifying the activation token.
        """
        request_serializer = RequestActivateAccount(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        
        validated_data = request_serializer.validated_data
        token = validated_data.get("token")
        if not token:
            return Response({"error_code": "MISSING_TOKEN", "detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = verify_token(token=token)
            
            user = User.objects.get(user_id=user_id)
            
            if user.is_active:
                return Response({"error_code": "USER_ALREADY_ACTIVE", "detail": "User is already active."}, status=status.HTTP_400_BAD_REQUEST)

            user.is_active = True
            user.save(update_fields=["is_active"])

            return Response({"detail": "Account successfully activated."}, status=status.HTTP_200_OK)
        
        except ValueError:
            return Response({"error_code": "INVALID_TOKEN", "detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist:
            return Response({"error_code": "USER_NOT_FOUND", "detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        except SignatureExpired as e:
            logger.error(f"Expired token: {e}", exc_info=True)
            return Response({"error_code": "TOKEN_EXPIRED", "detail": "Activation token has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception("Error while activating user.", exc_info=e)
            return Response({"error_code": "INTERNAL_SERVER_ERROR", "detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='sign-in')
    def sign_in(self, request: Request):
        serializer = RequestSignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            validated_data = serializer.validated_data
            user = cast(User, validated_data)

            if not user.is_active:
                logger.warning(f"Inactive account: {user.email}")
                raise PermissionDenied(detail="Your account is not activated")
            
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            token = RefreshToken.for_user(user=user)
            
            token.payload["user"] = {
                "id": str(user.user_id),
                "email": user.email,
                "fullName": user.full_name,
                "isSuperUser": user.is_superuser,
                "role": {
                    "id": str(user.role.id) if user.role else None,
                    "name": user.role.name if user.role else None
                },
            }

            token_data = {
                "refresh": str(token),
                "access": str(token.access_token)
            }

            response_serializer = TokenResponseSerializer({"tokens": token_data})
            logger.info("TokenResponseSerializer data returned successfully")
            return Response(data=response_serializer.data, status=status.HTTP_200_OK)

        except AuthenticationFailed as e:
            logger.error(e, exc_info=True)
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        except PermissionDenied as e:
            logger.error(f"Permission denied: {str(e)}", exc_info=True)
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.exception(e, exc_info=True)
            return Response({"detail": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["post"], url_path="sign-out")
    def sign_out(self, request: Request):
        serializer = SignOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            token = serializer.validated_data.get("refresh")
            
            RefreshToken(token).blacklist()
            
            return Response(data={"detail": "You have signed out successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"failed to sign out: {e}", exc_info=True)
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

