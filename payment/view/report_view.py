import logging
from typing import cast
from django.http import HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import action

from abstracts.enums.payment_category import PaymentCategory
from conference.models import Conference
from payment.enums.payment_status import PaymentStatus
from payment.models import Payment
from payment.serializers import ConferencePaymentReportSerializer

from user.enums.role import ROLE
from user.models import User

logger = logging.getLogger(__name__)


class ConferencePaymentReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get a list of conference payment reports (non-paginated)",
        operation_summary="Conference Payment Report",
        method="get",
        tags=["Payment"],
        manual_parameters=[
            openapi.Parameter(
                'conference_id',
                openapi.IN_QUERY,
                description="Conference ID",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'payment_status',
                openapi.IN_QUERY,
                description="Payment status filter",
                type=openapi.TYPE_STRING,
                enum=PaymentStatus.values()
            ),
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Payment category filter",
                type=openapi.TYPE_STRING,
                enum=PaymentCategory.values()
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of payment reports",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'payment_id': openapi.Schema(type=openapi.TYPE_STRING),
                            'user': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'affiliation': openapi.Schema(type=openapi.TYPE_STRING),
                                    'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                                    'country': openapi.Schema(type=openapi.TYPE_STRING),
                                    'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            ),
                            'abstract': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                nullable=True,
                                properties={
                                    'abstract_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'sub_theme': openapi.Schema(type=openapi.TYPE_STRING),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'authors': openapi.Schema(type=openapi.TYPE_STRING),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'keywords': openapi.Schema(type=openapi.TYPE_STRING),
                                    'document': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'sent_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', nullable=True),
                                    'comment': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'is_payment_done': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                    'user': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'middle_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                                            'country': openapi.Schema(type=openapi.TYPE_STRING),
                                            'occupation': openapi.Schema(type=openapi.TYPE_STRING),
                                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    ),
                                }
                            ),
                            'conference': openapi.Schema(type=openapi.TYPE_STRING),
                            'amount': openapi.Schema(type=openapi.TYPE_STRING),
                            'payment_slip': openapi.Schema(type=openapi.TYPE_STRING),
                            'comment': openapi.Schema(type=openapi.TYPE_STRING),
                            'status': openapi.Schema(type=openapi.TYPE_STRING),
                            'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        }
                    )
                )
            ),
            400: openapi.Response(
                description="Bad request - Missing or invalid conference ID",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Conference ID is required.")
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized - User is not an organizer",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="You are not authorized to perform this task")
                    }
                )
            ),
            404: openapi.Response(
                description="Conference not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Conference not found.")
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def conference_payment_report(self, request: HttpRequest):
        user = cast(User, request.user)

        if not request.user.is_authenticated or user.role not in [
            ROLE.ORGANIZER.value,
            ROLE.BURSAR.value,
            ROLE.ADMIN.value
        ]:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )

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
