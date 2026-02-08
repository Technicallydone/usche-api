import logging
from typing import cast
from django.http import HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from abstracts.enums.payment_category import PaymentCategory
from conference.models import Conference
from payment.enums.payment_status import PaymentStatus
from payment.models import Payment
from payment.serializers import ConferencePaymentReportSerializer

from user.models import User

logger = logging.getLogger(__name__)


class ConferencePaymentReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def conference_payment_report(self, request: HttpRequest):
        user = cast(User, request.user)

        conference_id = request.GET.get("conference_id")
        payment_status = request.GET.get("payment_status")
        category = request.GET.get("category")

        if not conference_id:
            return Response(
                data={"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)

            if conference is None:
                return Response(
                    data={"detail": "Conference not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            payments = Payment.conference_payment_report(
                conference=conference,
                status=payment_status,
                category=category
            )

            response_serializer = ConferencePaymentReportSerializer(payments, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error while retrieving paid abstracts for user {user.user_id}: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
