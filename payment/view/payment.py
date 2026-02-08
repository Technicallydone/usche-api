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
from payment.models import Payment
from payment.serializers import PaymentStatusUpdateSerializer, CompletedPaymentSerializer, UploadPaymentSlipSerializer, RequestPaymentDetailSerializer, PaymentSerializer
from payment.tasks import process_payment_approval
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
        """Complete a payment for an abstract and mark it as approved."""
        organizer = cast(User, request.user)

        request_serializer = PaymentStatusUpdateSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {"detail": "Invalid payment data."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            with transaction.atomic():
                payment_id = request_serializer.validated_data.get("payment_id")
                
                payment = Payment.mark_as_approved(payment_id=payment_id)

                if payment:
                    
                    if payment.abstract:
                        payment.abstract.mark_payment_done()
                    
                    Attendee.create_attendee(conference=payment.conference, participant=payment.user)
                    
                    process_payment_approval.delay({
                        "user_id": str(payment.user.user_id)
                    })
                    
                    return Response(
                        {"detail": "Payment completed successfully"},
                        status=status.HTTP_200_OK
                    )

                return Response(
                    {"detail": "Abstract not found or payment failed to mark as completed."},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error while completing payment: {e}")
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def reject_payment(self, request: HttpRequest):
        """Reject a payment with an optional comment."""
        user = cast(User, request.user)

        request_serailizer = PaymentStatusUpdateSerializer(data=request.data)
        request_serailizer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                payment = Payment.mark_as_rejected(
                    payment_id=request_serailizer.validated_data.get("payment_id"), 
                    comment=request_serailizer.validated_data.get("comment")
                )
                
                if payment:
                    send_payment_rejection_email(user=payment.user, comment=request_serailizer.validated_data.get("comment"))
                    return Response(data={"detail": "Payment rejected successfully"}, status=status.HTTP_200_OK)
                return Response({"detail": "Payment not found or already processed"}, status=status.HTTP_404_NOT_FOUND)

        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=False, methods=['get'])
    def pending_payments(self, request: HttpRequest):
        user = cast(User, request.user)
        
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