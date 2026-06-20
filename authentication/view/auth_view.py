from datetime import timedelta
import logging
from typing import cast
from django.core.signing import SignatureExpired
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.request import Request
from authentication.serializers import (
    RequestSignInSerializer,
    TokenResponseSerializer,
    SignOutSerializer,
    RequestActivateAccount,
    RequestNewToken,
    RequestChangePasswordSerializer,
    ForgotPasswordRequestSerializer,
    RequestRegistration
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.auth import TokenAuthentication
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from django.contrib.auth import authenticate
from services.email.tasks import send_email_task
from usche_app import settings
from user.enums.permission_enums import AppPermissionEnum
from user.model.user_model import User
from user.permissions import HasAppPermission
from utils.access_token import generate_token, verify_token
from django.utils import timezone

logger = logging.getLogger(__name__)

class AuthenticationViewSet(viewsets.ViewSet):
    MAX_FAILED_ATTEMPTS = 5
    LOCK_DURATION_MINUTES = 15
    
    permission_classes = [HasAppPermission]
    
    permission_mapping = {
        'sign_out': AppPermissionEnum.SIGN_OUT.value,
        'change_password': None,
        'forgot_password': None,
        'new_activation_email': None,
        'activate_account': None,
        'sign_in': None,
        'sign_up': None,
    }
    
    authentication_classes = [
        TokenAuthentication,
        JWTAuthentication,
    ]
    
    @action(detail=False, methods=['post'], url_path='accounts/reset-password')
    def change_password(self, request: Request):
        
        request_serializer = RequestChangePasswordSerializer(data=request.data)
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
                subject="USCHe Account Password Successfully Updated",
                to=user.email,
                greeting=f"Hello {user.first_name},",
                lines=[
                    "This is a confirmation that the password for your USCHe account has been successfully updated.",
                    "If you made this change, no further action is required.",
                    "If you did not make this change, please reset your password using the secure link below or contact the USCHe support team for assistance."
                ],
                salutations=["Regards,", "USCHe Support Team"],
                button_text="Access Your Account",
                button_url=f"{settings.FRONTEND_BASE_URL}/auth",
                footer_text="© 2026 USCHe - University of Dodoma"
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

    @action(detail=False, methods=['post'], url_path='accounts/forgot-password')
    def forgot_password(self, request: Request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            user = User.get_user_by_email(email=validated_data.get('email'))

            if user is None:
                return Response(data={"detail": "User with given email does not exist"}, status=status.HTTP_404_NOT_FOUND)

            with transaction.atomic():
                token = generate_token(user=user)
                if not token:
                    raise Exception("Failed to generate token")

                # Use the generic send_email_task.delay
                send_email_task.delay(
                    subject="Password Reset Request",
                    to=user.email,
                    greeting=f"Hello {user.first_name},",
                    lines=[
                        "A password reset request was received for your USCHe account.",
                        "If you initiated this request, please follow the link below to set a new password.",
                        "If you do not recognize this activity, you may disregard this message. No changes will be made to your account unless the password reset process is completed."
                    ],
                    salutations=[
                        "Thank you,",
                        "USCHe Account Services"
                    ],
                    button_text="Continue Password Reset",
                    button_url=f"{settings.FRONTEND_BASE_URL}/auth/reset-password/{token}",
                    footer_text="This email was sent automatically. Please do not reply to this message."
                )

                return Response(
                    data={"detail": "A password reset request has been received. If the email provided is associated with an account, you will receive instructions shortly to reset your password."},
                    status=status.HTTP_200_OK
                )
            return Response(data={"detail": "Failed to queue reset password link, please try again"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error occurred during reset password email: {str(e)}", exc_info=True)
            return Response(
                data={"detail": "An internal server error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=False, methods=['post'], url_path='accounts/request-activation-link')
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
                subject="Confirm Your Email Address",
                to=user.email,
                greeting=f"Hello {user.first_name},",
                lines=[
                    "Thank you for creating a USCHe account.",
                    "To complete your account setup, please confirm that this email address belongs to you by using the button below.",
                    "After confirmation, you will be able to access USCHe services and continue using your account.",
                    "If you did not create a USCHe account, no further action is required and you may safely ignore this message."
                ],
                salutations=[
                    "Thank you,",
                    "USCHe Account Services"
                ],
                button_text="Confirm Email Address",
                button_url=f"{settings.FRONTEND_BASE_URL}/auth/activate/{token}",
                footer_text="This email was sent automatically regarding your USCHe account. Please do not reply to this message."
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

    @action(detail=False, methods=['post'], url_path='accounts/activate')
    def activate_account(self, request: Request):
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
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                raise AuthenticationFailed("Invalid credentials")

            if user.locked_until and user.locked_until > timezone.now():
                remaining = (user.locked_until - timezone.now()).seconds // 60
                raise PermissionDenied(
                    f"Account locked due to multiple failed login attempts. Try again in {remaining} minutes."
                )

            # Authenticate the user
            authenticated_user = authenticate(email=email, password=password)
            if not authenticated_user:
                # Increment failed attempts
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                    user.locked_until = timezone.now() + timedelta(minutes=self.LOCK_DURATION_MINUTES)
                    user.failed_login_attempts = 0  # reset after locking
                user.save(update_fields=["failed_login_attempts", "locked_until"])
                raise AuthenticationFailed("Invalid credentials")

            # Check if user is active
            if not authenticated_user.is_active:
                raise PermissionDenied("Your account is not activated")

            # Successful login → reset failed attempts
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = timezone.now()
            user.save(update_fields=["failed_login_attempts", "locked_until", "last_login"])

            # Generate JWT token
            token = RefreshToken.for_user(authenticated_user)
            token.payload["user"] = {
                "id": str(user.user_id),
                "email": user.email,
                "fullName": user.full_name,
                "isSuperUser": user.is_superuser,
                "role": {
                    "id": str(user.role.id) if user.role else None,
                    "name": user.role.name if user.role else None
                },
                "permissions": list(user.role.permissions.values_list("code_name", flat=True)) if user.role else []
            }

            token_data = {"refresh": str(token), "access": str(token.access_token)}
            response_serializer = TokenResponseSerializer({"tokens": token_data})

            return Response(data=response_serializer.data, status=status.HTTP_200_OK)

        except AuthenticationFailed as e:
            logger.warning(f"Authentication failed for {request.data.get('email')}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionDenied as e:
            logger.warning(f"Permission denied for {request.data.get('email')}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Unexpected error during sign-in for {request.data.get('email')}: {str(e)}")
            return Response({"detail": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='sign-up')
    def sign_up(self, request: Request):
        serializer = RequestRegistration(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")

        try:
            # Check if user exists
            try:
                user = User.objects.get(email=email)
                
                if not user.is_active:
                    token = generate_token(user=user)
                    # Resend activation email
                    subject = "USCHe Account"

                    recipient = user.email

                    greeting = f"Hello {user.first_name},"

                    lines = [
                    "Your USCHe account is available.",
                    "Please use the link below to continue."
                    ]

                    salutations = [
                    "USCHe"
                    ]

                    button_text = "Continue"

                    button_url = f"{settings.FRONTEND_BASE_URL}/auth/activate/{token}"

                    footer_text = "University of Dodoma"



                    send_email_task.delay(
                        subject=subject,
                        to=recipient,
                        greeting=greeting,
                        lines=lines,
                        salutations=salutations,
                        button_text=button_text,
                        button_url=button_url,
                        footer_text=footer_text
                    )

                    return Response(
                        data={"detail": "Your account is not activated yet. We have resent the activation email."},
                        status=status.HTTP_200_OK,
                    )
                else:
                    # Already active
                    return Response(
                        data={"detail": "This email is already registered and active. Please login."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except User.DoesNotExist:
                # Create new user
                with transaction.atomic():
                    middle_name = validated_data.get("middle_name")
                    middle_name = middle_name if middle_name else None
                    user = User.create_user(
                        title=validated_data.get("title"),
                        first_name=validated_data.get("first_name"),
                        middle_name=middle_name,
                        last_name=validated_data.get("last_name"),
                        phone_number=validated_data.get("phone_number"),
                        email=email,
                        country=validated_data.get("country"),
                        password=validated_data.get("password"),
                        affiliation=validated_data.get("affiliation"),
                        occupation=validated_data.get("occupation"),
                    )
                    
                token = generate_token(user=user)

                # Send activation email
                subject = "USCHe Registration"
                recipient = user.email
                greeting = f"Hello {user.first_name},"

                lines = [
                "Thank you for registering with USCHe.",
                "Please use the link below to continue."
                ]

                salutations = [
                "USCHe"
                ]

                button_text = "Continue"

                button_url = f"{settings.FRONTEND_BASE_URL}/auth/activate/{token}"

                footer_text = "University of Dodoma"



                send_email_task.delay(
                    subject=subject,
                    to=recipient,
                    greeting=greeting,
                    lines=lines,
                    salutations=salutations,
                    button_text=button_text,
                    button_url=button_url,
                    footer_text=footer_text
                )

                return Response(
                    data={"detail": "You have successfully registered. A confirmation email has been sent to you for activation."},
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            logger.error(f"Error occurred during registration: {str(e)}", exc_info=True)
            return Response(
                data={"detail": "An internal server error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=["post"], url_path="sign-out",
            permission_classes=[permissions.IsAuthenticated, HasAppPermission])
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

