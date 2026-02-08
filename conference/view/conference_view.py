from decimal import Decimal, InvalidOperation
import logging
import os
from typing import cast
from django.http import FileResponse, Http404, HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from conference.models import ConferenceScheduleDocument
from conference.models import Conference
from conference.serializers import ConferenceDetailSerializer, RequestJoinConferenceSerializer
from rest_framework.decorators import action

from django.db import transaction

from payment.models import Payment
from usche_app import settings
from user.model.user_model import User
from utils.qr_code_generator import generate_qr_code

logger = logging.getLogger(__name__)

class ConferenceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def join(self, request: HttpRequest):
        """Handles user requests to join a conference by uploading a payment slip."""
        if not request.user.is_authenticated:
            return Response(
                data={"detail": "You are not authorized to perform this task, please login and provide authentication credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        conference_id = request.GET.get('conference_id')
        
        if not conference_id:
            return Response(data={"detail": "Conference ID is mandatory"}, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = cast(User, request.user)
        serializer = RequestJoinConferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment_slip = serializer.validated_data['payment_slip']

            try:
                amount = Decimal(serializer.validated_data["amount"])
            except InvalidOperation:
                return Response(
                    {"detail": "Invalid amount format. Please provide a valid decimal number."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            conference = Conference.get_conference_by_id(conference_id=conference_id)

            if not conference:
                return Response({"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)

            if conference.is_conference_outdated():
                return Response(
                    data={"detail": "We regret to inform you that the conference has already ended."},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                if Payment.has_pending_payment(user=user, conference=conference):
                    return Response(
                        data={"detail": "You have a pending payment that requires approval. Please be patient while we process your payment slip. If you are an agent, please don't hesitate to contact support."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                Payment.create_payment(
                    user=user,
                    conference=conference,
                    amount=amount,
                    payment_slip=payment_slip
                )

            return Response(
                {"detail": "Payment slip uploaded successfully. We will notify you via email once your payment slip has been verified."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Failed to upload payment slip for joining the conference: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def read(self, request: HttpRequest):
        year = request.GET.get('year')
        
        try:
            conference = Conference.get_conference(year=year)

            if not conference:
                return Response({"detail": "No conference available"}, status=status.HTTP_404_NOT_FOUND)

            serializer = ConferenceDetailSerializer(conference)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="conference_schedule/(?P<conference_id>[^/.]+)/download-pdf")
    def download_conference_pdf(self, request, conference_id=None):
        try:
            document = ConferenceScheduleDocument.objects.filter(
                conference__conference_id=conference_id,
                is_active=True
            ).first()
            if not document or not document.file:
                raise Http404("No active PDF found for this conference.")

            return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.title + ".pdf")

        except ConferenceScheduleDocument.DoesNotExist:
            raise Http404("PDF not found.")

    @action(detail=False, methods=["get"], url_path="conference_schedule/(?P<conference_id>[^/.]+)/qr-code")
    def conference_schedule_qr(self, request: HttpRequest, conference_id=None):
        
        download_url = f"{settings.FRONTEND_BASE_URL}/conference/schedule/{conference_id}/download"
        img_io = generate_qr_code(download_url)
        return FileResponse(img_io, content_type='image/png')
