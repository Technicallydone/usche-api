import logging
from typing import cast
import uuid
from django.core.signing import SignatureExpired
from rest_framework import authentication, permissions, status, viewsets
from authentication.enums.error_code import ActivationErrorCodes
from authentication.serializers import RequestSignInSerializer, TokenResponseSerializer, SignOutSerializer, RequestActivateAccount, RequestNewToken, RequestChangePasswordSerailizer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.auth import TokenAuthentication
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from authentication.tasks import process_reset_password_email
from usche_app import settings
from user.model.user import User
from utils.beem_sms import BeemSMSClient
from utils.send_email import send_activation_email
from utils.access_token import generate_token, verify_token
from django.core.mail import BadHeaderError
from django.utils import timezone

logger = logging.getLogger(__name__)

class AuthenticationViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = [
        TokenAuthentication,
        JWTAuthentication,
    ]
    

    @swagger_auto_schema(
        operation_description="Change password after reset password email sent to the user by providing token and new password",
        operation_summary="Change password on forgot password",
        method="post",
        tags=["Authentication"],
        request_body=RequestChangePasswordSerailizer,
        responses={
            200: openapi.Response(
                description="Password successfully changed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING, enum=[
                            ActivationErrorCodes.INVALID_TOKEN, 
                            ActivationErrorCodes.MISSING_TOKEN,
                            ActivationErrorCodes.TOKEN_EXPIRED,
                            ActivationErrorCodes.USER_NOT_FOUND
                        ]),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: openapi.Response(
                description="User not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
        }
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request, email = None):
        
        request_serializer = RequestChangePasswordSerailizer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        validated_data = request_serializer.validated_data
        
        token = validated_data.get("token")
        
        if not token:
            return Response({"error_code": "MISSING_TOKEN", "detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = verify_token(token=token)
            
            user = User.get_user_by_id(user_id=user_id)
            
            if user is None:
                return Response(data={"error_code": "USER_NOT_FOUND", "detail": "User with given email does not exist"}, status=status.HTTP_404_NOT_FOUND)
            
            user.set_password(raw_password=validated_data.get("new_password"))
            user.save(update_fields=["password"])
            return Response({"detail": "Password changes successfully, you can login to your password"}, status=status.HTTP_200_OK)

        except ValueError:
            return Response({"error_code": "INVALID_TOKEN", "detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        except SignatureExpired as e:
            logger.error(f"Expired token: {e}", exc_info=True)
            return Response({"error_code": "TOKEN_EXPIRED", "detail": "Activation token has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception("Error while activating user.", exc_info=e)
            return Response({"error_code": "INTERNAL_SERVER_ERROR", "detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Request reset password email on forgot login password",
        operation_summary="Forgot password",
        method="post",
        tags=["Authentication"],
        responses={
            200: openapi.Response(
                description="Resent password request email successfully sent",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request | Email tot provided",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: openapi.Response(
                description="User not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'email',
                openapi.IN_PATH,
                description="Valid email",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
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
            
    
    @swagger_auto_schema(
        operation_description="Request a new token using the provided activation token.",
        operation_summary="Request New Token",
        method="post",
        tags=["Authentication"],
        request_body=RequestNewToken,
        responses={
            200: openapi.Response(
                description="Token successfully sent",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING, enum=[
                            ActivationErrorCodes.INVALID_TOKEN, 
                            ActivationErrorCodes.MISSING_TOKEN
                        ]),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: openapi.Response(
                description="User not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
        }
    )
    @action(detail=False, methods=['post'])
    def new_activation_email(self, request):
        """
        Sent new activation email
        """
        request_serializer = RequestNewToken(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        
        validated_data = request_serializer.validated_data
        token = validated_data.get("token")

        if not token:
            return Response({"error_code": "MISSING_TOKEN", "detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            
            sms = BeemSMSClient()
            
            user_id = verify_token(token=token, max_age=31_536_000)
            
            user = User.objects.get(user_id=user_id)
            
            if user.is_active:
                return Response({"error_code": "USER_ALREADY_ACTIVE", "detail": "User is already active."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                send_activation_email(user)
                token = generate_token(user=user)
                
                try:
                    message = (
                        f"Dear {user.title} {user.last_name},\n\n"
                        "Your registration is successful. Please click the link below to activate your account:\n\n"
                        f"link: {settings.FRONTEND_BASE_URL}/activate/{token}"
                    )


                    sms_response = sms.send_sms(
                        message=message,
                        recipients=[user.phone_number]
                    )

                    logger.info(f"SMS sent successfully: {sms_response}")
                except Exception as sms_error:
                    logger.error(f"SMS sending failed: {str(sms_error)}", exc_info=True)
                
                return Response(
                    data={"detail": "A new activation email has been sent."}, 
                    status=status.HTTP_201_CREATED
                )
            except BadHeaderError as bhe:
                logger.error(f"Email sending failed due to BadHeaderError: {str(bhe)}", exc_info=True)
                return Response(data={"detail": "Invalid email header. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}", exc_info=True)
                return Response(data={"detail": "Failed to send activation email. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except ValueError:
            return Response({"error_code": "INVALID_TOKEN", "detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist:
            return Response({"error_code": "USER_NOT_FOUND", "detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("Error while activating user.", exc_info=e)
            return Response({"error_code": "INTERNAL_SERVER_ERROR", "detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @swagger_auto_schema(
        operation_description="Activate a user account using the provided activation token.",
        operation_summary="Activate Account",
        method="post",
        tags=["Authentication"],
        request_body=RequestActivateAccount,
        responses={
            200: openapi.Response(
                description="Account successfully activated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING, enum=[
                            ActivationErrorCodes.INVALID_TOKEN, 
                            ActivationErrorCodes.MISSING_TOKEN,
                            ActivationErrorCodes.TOKEN_EXPIRED
                        ]),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: openapi.Response(
                description="User not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
        }
    )
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

    @swagger_auto_schema(
        operation_description="Request login by submitting username and password",
        operation_summary="Request Login",
        method="post",
        tags=["Authentication"],
        request_body=RequestSignInSerializer,
        responses={
            200: TokenResponseSerializer,
            401: openapi.Response(
                description="Invalid credentials",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            403: openapi.Response(
                description="Inactive account",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
        }
    )
    @action(detail=False, methods=['post'])
    def sign_in(self, request):
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
                "full_name": user.full_name,
                "roles": [user.role],
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



class SignOutViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SignOutSerializer
    
    @swagger_auto_schema(
        operation_description="Sign out the authenticated user and blacklist the token",
        operation_summary="Sign out",
        tags=["Authentication"],
        method="post",
        request_body=SignOutSerializer,
        responses={
            200: openapi.Response(
                description="Successul sign out",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
        }
    )
    @action(detail=False, methods=["post"])
    def sign_out(self, request):
        serializer = SignOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            token = serializer.validated_data.get("refresh")
            
            RefreshToken(token).blacklist()
            
            return Response(data={"detail": "You have signed out successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"failed to sign out: {e}", exc_info=True)
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)