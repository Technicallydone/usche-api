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
    PaymentStatusUpdateSerializer,
    CompletedPaymentSerializer,
    UploadPaymentSlipSerializer,
    RequestPaymentDetailSerializer,
    PaymentSerializer,
    PaymentQuerySerializer,
    PaymentDecisionSerializer
)
from payment.tasks import process_payment_approval
from services.email.tasks import send_email_task
from usche_app import settings
from django.db import transaction

from user.enums.permission_enums import AppPermissionEnum
from user.models import User
from user.permissions import HasAppPermission
from utils.beem_sms import BeemSMSClient
from utils.send_email import send_payment_rejection_email
from rest_framework.pagination import PageNumberPagination


logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        'list': AppPermissionEnum.READ_PAYMENTS.value,
        "approved": AppPermissionEnum.READ_PAYMENTS.value,
        "pending_payments": AppPermissionEnum.READ_PAYMENTS.value,
        "retrieve_payment": AppPermissionEnum.READ_OWN_PAYMENTS.value,
        "upload_payment_slip": AppPermissionEnum.CREATE_PAYMENTS.value,
        "read_payment_slip": AppPermissionEnum.READ_PAYMENTS.value,
        "complete_payment": AppPermissionEnum.APPROVE_PAYMENTS.value,
        "reject_payment": AppPermissionEnum.REJECT_PAYMENTS.value,
        'download_payment_slip': AppPermissionEnum.DOWNLOAD_PAYMENT_SLIP.value,
        'reject': AppPermissionEnum.REJECT_PAYMENTS.value,
        'approve': AppPermissionEnum.APPROVE_PAYMENTS.value
    }
    
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

                attendee, created = Attendee.objects.get_or_create(
                    conference=payment.conference,
                    participant=payment.user,
                    defaults={
                        "status": AttendeeStatus.ACTIVE.value,
                        "invitation_sent": False,
                    }
                )

                if not created:
                    attendee.status = AttendeeStatus.ACTIVE.value
                    attendee.save()

                payment.status = PaymentStatus.COMPLETED.value
                payment.comment = ""
                payment.rejected_by = None
                payment.save()

            logger.info(f"Payment {pk} approved by {request.user}")

            return Response(
                {
                    "detail": "Payment approved successfully and attendee activated"
                },
                status=status.HTTP_200_OK,
            )

        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error approving payment {pk}: {e}")
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
    
    @action(detail=False, methods=["get"])
    def approved(self, request: HttpRequest):
        
        conference_id = request.GET.get("conference_id")
        search_query = request.GET.get('search_query')
        
        if conference_id is None:
            return Response(data={"detail": "Conference id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Use the get_approved_payments method here
            payments = Payment.get_approved(conference=conference, search_query=search_query)
            
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(payments, request)
            
            if page is not None:
                response_serializer = CompletedPaymentSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)
            
            response_serializer = CompletedPaymentSerializer(payments, many=True)
            return Response(data=response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error while retrieving approved payments: {e}", exc_info=True)
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["post"])
    def retrieve_payment(self, request: HttpRequest):
        if not request.user.is_authenticated:
            return Response(data={"detail": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = cast(User, request.user)
        request_serializer = RequestPaymentDetailSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        
        conference_id = request_serializer.validated_data.get("conference_id")
        
        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            payment = Payment.get_payment(user=user, conference=conference)
            
            if payment is None:
                return Response(data={"detail": "You don't have any payment to this conference"}, status=status.HTTP_404_NOT_FOUND)
            
            response_serializer = PaymentSerializer(payment, many=False)
            return Response(data=response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error while retrieving payment detail: {e}", exc_info=True)
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
            print(pk)
            payment = Payment.objects.get(pk=pk)
            
            print(payment)

            if not payment.payment_slip:
                return Response(
                    {"detail": "No payment slip uploaded"},
                    status=status.HTTP_404_NOT_FOUND,
                )
                
            print(payment)

            file_path = payment.payment_slip.path
            
            print(file_path)

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
            print(f"hereeeee: {str(e)}")
            logger.error(f"Error downloading payment slip: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['post'], url_path='complete-payment')
    def complete_payment(self, request: HttpRequest):
        """Complete a payment for an abstract, mark it as approved and notify the user."""

        serializer = PaymentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_id = serializer.validated_data.get("payment_id")

        try:
            with transaction.atomic():

                payment = Payment.mark_as_approved(payment_id=payment_id)

                if not payment:
                    return Response(
                        {"detail": "Payment not found or already processed."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                if payment.abstract:
                    payment.abstract.mark_payment_done()

                Attendee.create_attendee(
                    conference=payment.conference,
                    participant=payment.user
                )

            # Send approval email AFTER transaction succeeds
            send_email_task.delay(
                subject="Payment Approved - USChE Conference",
                to=payment.user.email,
                greeting=f"Hello {payment.user.first_name},",
                lines=[
                    "We are pleased to inform you that your payment has been successfully approved.",
                    "Your conference registration is now confirmed.",
                    "We look forward to your participation."
                ],
                salutations=["Best regards,", "The USChE Finance Team"],
                button_text="View Conference Details",
                button_url=f"{settings.FRONTEND_BASE_URL}/dashboard",
                footer_text="© 2026 USChE - University of Dodoma"
            )

            process_payment_approval.delay({
                "user_id": str(payment.user.user_id)
            })

            return Response(
                {"detail": "Payment completed successfully and user notified."},
                status=status.HTTP_200_OK
            )

        except Exception:
            logger.exception("Error while completing payment.")
            return Response(
                {"detail": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def reject_payment(self, request: HttpRequest):
        """Reject a payment and notify the user via email."""

        user = cast(User, request.user)

        serializer = PaymentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_id = serializer.validated_data.get("payment_id")
        comment = serializer.validated_data.get("comment")

        try:
            with transaction.atomic():

                payment = Payment.objects.select_for_update().get(payment_id=payment_id)

                if payment.status != PaymentStatus.PENDING.value:
                    return Response(
                        {"detail": "Payment has already been processed."},
                        status=status.HTTP_409_CONFLICT
                    )

                payment.status = PaymentStatus.REJECTED.value
                payment.comment = comment
                payment.rejected_by = user
                payment.save(update_fields=["status", "comment", "rejected_by"])

            send_email_task.delay(
                subject="Payment Rejected - USChE Conference",
                to=payment.user.email,
                greeting=f"Hello {payment.user.first_name},",
                lines=[
                    "We regret to inform you that your recent payment submission has been rejected.",
                    f"Reason: {comment or 'No reason was provided.'}",
                    "Please review the issue and submit a new payment."
                ],
                salutations=["Best regards,", "The USChE Finance Team"],
                button_text="Submit New Payment",
                button_url=f"{settings.FRONTEND_BASE_URL}/auth",
                footer_text="© 2026 USChE - University of Dodoma"
            )

            return Response(
                {"detail": "Payment rejected successfully and user notified."},
                status=status.HTTP_200_OK
            )

        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception:
            logger.exception("Error while rejecting payment.")
            return Response(
                {"detail": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def pending_payments(self, request: HttpRequest):
        conference_id = request.GET.get("conference_id")
        search_query = request.GET.get("search_query")
        
        
        if not conference_id:
            return Response(
                data={"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            
            if conference is None:
                return Response(data={"detail": "Conference not found."}, status=status.HTTP_404_NOT_FOUND)
            
            payments = Payment.get_pending(conference=conference, search_query=search_query)
            
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(payments, request)
            
            if page is not None:
                response_serializer = PaymentSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)
            
            response_serializer = PaymentSerializer(payments, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error while retrieving pending payments: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )