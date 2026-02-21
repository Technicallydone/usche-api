import base64
from decimal import Decimal, InvalidOperation
import logging
import os
from typing import cast
from django.http import Http404, HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from abstracts.models import Abstract
from attendee.models import Attendee
from conference.models import Conference
from payment.enums.payment_status import PaymentStatus
from payment.models import Payment
from payment.serializers import PaymentStatusUpdateSerializer, CompletedPaymentSerializer, UploadPaymentSlipSerializer, RequestPaymentDetailSerializer, PaymentSerializer
from payment.tasks import process_payment_approval
from services.email.tasks import send_email_task
from usche_app import settings
from django.db import transaction

from user.models import User
from utils.beem_sms import BeemSMSClient
from utils.send_email import send_payment_rejection_email
from rest_framework.pagination import PageNumberPagination


logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
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

    @action(detail=False, methods=['get'], url_path='payment-slip/(?P<payment_slip_id>[^/]+)')
    def read_payment_slip(self, request: HttpRequest, payment_slip_id):
        """Retrieve a payment slip document as a base64 encoded string."""
        user = cast(User, request.user)

        try:
            payment = Payment.objects.get(payment_id=payment_slip_id)

            document_filename = payment.payment_slip.name
            document_path = os.path.join(settings.MEDIA_ROOT, document_filename)

            if not os.path.exists(document_path):
                raise Http404("Payment slip document not found")

            with open(document_path, 'rb') as doc_file:
                file_content = doc_file.read()

            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

            return Response(
                data={
                    "detail": "Payment slip document retrieved successfully",
                    "file_content": file_content_base64  
                },
                status=status.HTTP_200_OK
            )

        except Payment.DoesNotExist:
            logger.error(f"Payment slip document with ID {payment_slip_id} not found.")
            return Response(data={"detail": "Payment slip document not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error while retrieving payment slip document: {e}")
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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