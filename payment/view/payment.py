import base64
from decimal import Decimal, InvalidOperation
import logging
import os
from typing import cast
from django.http import FileResponse, Http404, HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.request import Request
from abstracts.models import Abstract
from attendee.enums.attendee_status import AttendeeStatus
from attendee.models import Attendee
from conference.models import Conference
from payment.enums.payment_status import PaymentStatus
from payment.models import Payment
from payment.serializers import (
    UploadPaymentSlipSerializer,
    PaymentSerializer,
    PaymentQuerySerializer,
    PaymentDecisionSerializer,
    RequestJoinConferenceSerializer,
    MyPaymentQuerySerializer
)
from services.email.tasks import send_email_task
from usche_app import settings
from django.db import transaction

from user.enums.permission_enums import AppPermissionEnum
from user.models import User
from user.permissions import HasAppPermission
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404


logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        'list': AppPermissionEnum.READ_PAYMENTS.value,
        "approved": AppPermissionEnum.READ_PAYMENTS.value,
        "pending_payments": AppPermissionEnum.READ_PAYMENTS.value,
        "retrieve_payment": [AppPermissionEnum.READ_OWN_PAYMENTS.value, AppPermissionEnum.READ_PAYMENTS],
        "upload_payment_slip": AppPermissionEnum.CREATE_PAYMENTS.value,
        "read_payment_slip": AppPermissionEnum.READ_PAYMENTS.value,
        "complete_payment": AppPermissionEnum.APPROVE_PAYMENTS.value,
        "reject_payment": AppPermissionEnum.REJECT_PAYMENTS.value,
        'download_payment_slip': AppPermissionEnum.DOWNLOAD_PAYMENT_SLIP.value,
        'reject': AppPermissionEnum.REJECT_PAYMENTS.value,
        'approve': AppPermissionEnum.APPROVE_PAYMENTS.value,
        'my_payments': AppPermissionEnum.READ_OWN_PAYMENTS.value,
        'create_payment': AppPermissionEnum.REQUEST_JOIN_CONFERENCE.value,
    }
    
    @action(detail=True, methods=["post"], url_path="request-join")
    def request_join_conference(self, request: Request, pk=None):
        serializer = RequestJoinConferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            conference = get_object_or_404(Conference, conference_id=pk)

            payment = Payment.objects.create(
                user=request.user,
                conference=conference,
                amount=serializer.validated_data["amount"],
                payment_slip=serializer.validated_data["payment_slip"],
                status=PaymentStatus.PENDING.value,
            )

            # EMAIL (NO BUTTON)
            send_email_task.delay(
                subject="Conference Join Request Received",
                to=payment.user.email,
                greeting=f"Hello {payment.user.first_name},",
                lines=[
                    "We have received your conference join request successfully.",
                    f"Amount: {payment.amount}",
                    "Your request is now under review by the finance team.",
                ],
                salutations=["Best regards,", "Conference Secretariat"],
                footer_text="© 2026 Conference Management System",
            )

            return Response(
                {"detail": "Join request submitted", "id": payment.payment_id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating payment request: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=True, methods=['get'], url_path='retrieve')
    def retrieve_payment(self, request: Request, pk=None):
        try:
            payment = get_object_or_404(
                Payment,
                payment_id=pk
            )

            serializer = PaymentSerializer(payment)

            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error retrieving payment: {e}")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=['get'], url_path='mine')
    def my_payments(self, request: Request):
        user = cast(User, request.user)
        
        query_serializer = MyPaymentQuerySerializer(
                data=request.query_params
            )
        query_serializer.is_valid(raise_exception=True)

        try:
            payments = Payment.objects.filter(user=user)

            status_filter = query_serializer.validated_data.get("status")

            if status_filter:
                payments = payments.filter(status=status_filter)

            payments = payments.order_by("-timestamp")

            paginator = PageNumberPagination()
            paginator.page_size_query_param = "page_size"

            page = paginator.paginate_queryset(payments, request)

            if page is not None:
                serializer = PaymentSerializer(page, many=True)

                return paginator.get_paginated_response(serializer.data)

            serializer = PaymentSerializer(payments, many=True)

            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error retrieving my payments: {e}")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request: Request, pk=None):
        serializer = PaymentDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(pk=pk)

                if payment.status != PaymentStatus.PENDING.value:
                    return Response(
                        {"detail": "Only pending payments can be modified."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                payment.status = PaymentStatus.REJECTED.value
                payment.comment = serializer.validated_data.get('comment')
                payment.rejected_by = request.user
                payment.save()

            logger.info(f"Payment {pk} rejected by {request.user}")
            
            send_email_task.delay(
                subject="Payment Rejected - USChE Conference",
                to=payment.user.email,
                greeting=f"Hello {payment.user.first_name},",
                lines=[
                    "We regret to inform you that your recent payment submission has been rejected.",
                    f"Reason: {serializer.validated_data.get('comment') or 'No reason was provided.'}",
                    "Please review the issue and submit a new payment."
                ],
                salutations=["Best regards,", "The USChE Finance Team"],
                button_text="Submit New Payment",
                button_url=f"{settings.FRONTEND_BASE_URL}/dashboard/conference/payments/{payment.payment_id}/details",
                footer_text="© 2026 USChE - University of Dodoma"
            )

            return Response(
                {"detail": "Payment rejected successfully"},
                status=status.HTTP_200_OK,
            )

        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error rejecting payment {pk}: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request: Request, pk=None):
        try:
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(pk=pk)

                if payment.status != PaymentStatus.PENDING.value:
                    return Response(
                        {"detail": "Only pending payments can be modified."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                attendee = Attendee.objects.filter(
                    conference=payment.conference,
                    participant=payment.user
                ).first()

                if attendee:
                    attendee.status = AttendeeStatus.ACTIVE.value
                    attendee.invitation_sent = False
                    attendee.save(
                        update_fields=[
                            "status",
                            "invitation_sent",
                        ]
                    )

                else:
                    attendee = Attendee.objects.create(
                        conference=payment.conference,
                        participant=payment.user,
                        status=AttendeeStatus.ACTIVE.value,
                        invitation_sent=False,
                    )

                payment.status = PaymentStatus.COMPLETED.value
                payment.comment = ""
                payment.rejected_by = None

                payment.save(
                    update_fields=[
                        "status",
                        "comment",
                        "rejected_by",
                    ]
                )

            logger.info(
                f"Payment {pk} approved by {request.user}"
            )

            send_email_task.delay(
                subject="Payment Approved - USChE Conference",
                to=payment.user.email,
                greeting=f"Hello {payment.user.first_name},",
                lines=[
                    (
                        "We are pleased to inform you that your "
                        "payment has been successfully approved."
                    ),
                    (
                        "Your conference registration "
                        "is now confirmed."
                    ),
                    (
                        "We look forward to your participation."
                    )
                ],
                salutations=[
                    "Best regards,",
                    "The USChE Finance Team"
                ],
                button_text="View Conference Details",
                button_url=(
                    f"{settings.FRONTEND_BASE_URL}"
                    f"/dashboard/conference/payments/"
                    f"{payment.payment_id}/details"
                ),
                footer_text="© 2026 USChE - University of Dodoma"
            )

            return Response(
                {
                    "detail": (
                        "Payment approved successfully "
                        "and attendee activated"
                    )
                },
                status=status.HTTP_200_OK,
            )

        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(
                f"Error approving payment {pk}: {e}",
                exc_info=True
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def list(self, request: Request):
        serializer = PaymentQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        conference_id = validated_data.get("conference_id")
        payment_status = validated_data.get("status")
        search = validated_data.get("search")

        try:
            conference = Conference.objects.get(conference_id=conference_id)

            payments = Payment.get_conference_payments(
                conference=conference,
                status=payment_status,
                search_query=search,
            )

            paginator = PageNumberPagination()
            paginator.page_size_query_param = "page_size"

            page = paginator.paginate_queryset(payments, request)

            if page is not None:
                serializer = PaymentSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = PaymentSerializer(payments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Conference.DoesNotExist:
            return Response(
                {"detail": "Conference not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=['post'], url_path='upload-payment-slip')
    def upload_payment_slip(self, request: HttpRequest):
        """Handles payment slip uploads"""
        
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = cast(User, request.user)
            serializer = UploadPaymentSlipSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            abstract_id = serializer.validated_data["abstract_id"]
            payment_slip = serializer.validated_data["payment_slip"]
            
            try:
                amount = Decimal(serializer.validated_data["amount"])
            except InvalidOperation:
                return Response(
                    {"detail": "Invalid amount format. Please provide a valid decimal number."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            abstract = Abstract.get_abstract_by_id(abstract_id=abstract_id)

            if not abstract:
                return Response(data={"detail": "Abstract does not exist"}, status=status.HTTP_404_NOT_FOUND)

            if not abstract.is_owned_by(user=user):
                return Response(data={"detail": "You don't have permission to upload payment slip for this abstract"}, status=status.HTTP_403_FORBIDDEN)

            if Payment.get_payment_by_abstract_payment(abstract=abstract).exists():
                return Response(data={"detail": "You have already uploaded your payment slip, please wait while we are processing your payment slip"}, status=status.HTTP_409_CONFLICT)

            Payment.create_payment(
                user=user,
                conference=abstract.sub_theme.theme.conference,
                amount=amount,
                payment_slip=payment_slip,
                abstract=abstract
            )

            return Response(
                {"detail": "Payment slip uploaded successfully"},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Unexpected error occurred while uploading payment slip: {e}")
            return Response(
                {"detail": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"], url_path="download-slip")
    def download_payment_slip(self, request: Request, pk=None):
        try:
            payment = Payment.objects.get(pk=pk)
            
            if not payment.payment_slip:
                return Response(
                    {"detail": "No payment slip uploaded"},
                    status=status.HTTP_404_NOT_FOUND,
                )
                
            file_path = payment.payment_slip.path
            
            if not os.path.exists(file_path):
                raise Http404("Payment slip not found")

            response = FileResponse(open(file_path, "rb"), as_attachment=True)

            filename = os.path.basename(file_path)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            return response

        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error downloading payment slip: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
