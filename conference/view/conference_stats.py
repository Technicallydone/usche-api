import logging
from typing import cast
from django.http import   HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import action
from abstracts.models import Abstract
from attendee.models import Attendee
from conference.models import Conference, TargetGroup
from payment.models import Payment
from theme.models import MainTheme, SubTheme
from user.enums.role import ROLE
from user.models import User

logger = logging.getLogger(__name__)

class ConferenceStatsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated,]
    
    
    @swagger_auto_schema(
        operation_description="Retrieve conference statistics",
        operation_summary="Conference Stats",
        method="get",
        tags=["Conference Stats"],
        responses={
            200: openapi.Response(
                description="Successfully conference stats retrieved",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "stats": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "conference": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "conference_name": openapi.Schema(type=openapi.TYPE_STRING, example="Annual Research Conference 2025"),
                                        "start_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-08-01"),
                                        "end_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-08-05"),
                                        "capacity": openapi.Schema(type=openapi.TYPE_INTEGER, example=500),
                                        "venue": openapi.Schema(type=openapi.TYPE_STRING, example="Kigali Convention Centre"),
                                        "total_sub_themes": openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                                        "total_target_groups": openapi.Schema(type=openapi.TYPE_INTEGER, example=8),
                                    }
                                ),
                                "attendees": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "total_users": openapi.Schema(type=openapi.TYPE_INTEGER, example=1500),
                                        "total_attendees": openapi.Schema(type=openapi.TYPE_INTEGER, example=1200),
                                    }
                                ),
                                "abstracts": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "total_abstracts": openapi.Schema(type=openapi.TYPE_INTEGER, example=300),
                                        "total_paid_abstracts": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
                                        "total_unpaid_abstracts": openapi.Schema(type=openapi.TYPE_INTEGER, example=100),
                                        "total_approved_abstracts": openapi.Schema(type=openapi.TYPE_INTEGER, example=180),
                                    }
                                ),
                                "payments": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "total_payments": openapi.Schema(type=openapi.TYPE_INTEGER, example=220),
                                        "total_join_requests": openapi.Schema(type=openapi.TYPE_INTEGER, example=250),
                                        "total_pending_join_requests": openapi.Schema(type=openapi.TYPE_INTEGER, example=30),
                                        "total_abstract_payments": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
                                    }
                                ),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request - Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid input")
                    }
                ),
            ),
            401: openapi.Response(
                description="Unauthorized - User must be authenticated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Authentication credentials were not provided")
                    }
                ),
            ),
            404: openapi.Response(
                description="Document not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Document with given id not found")
                    }
                ),
            ),
        }
    )
    @action(detail=False, methods=['get'])
    def conference_stats(self, request: HttpRequest):
        user = cast(User, request.user)
        
        allowed_roles = [ROLE.ORGANIZER.value, ROLE.ADMIN.value, ROLE.BURSAR.value]
        if user.role not in allowed_roles and not user.is_staff:
            return Response(data={"detail": "You are forbidden to read this information"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            conference = Conference.get_latest_conference()
            if conference is None:
                return Response(data={"detail": "NO conference found"}, status=status.HTTP_404_NOT_FOUND)
            
            """"
                Conference stats
                1. Total subthemes
                2. Total target groups
            """
            theme = MainTheme.get_theme_by_conference(conference)
            
            if theme is None:
                return Response(data={"detail": f"No main theme found for {conference.conference_name}"}, status=status.HTTP_404_NOT_FOUND)
            
            total_sub_theme = SubTheme.get_total_theme_subthemes(theme=theme)
            
            total_conference_target_groups = TargetGroup.total_conference_target_groups(conference=conference)
            
        
            """
                Attendee stats
                1. Total user in te system
                2. Total attendee counting from the attendee
            """
            
            total_users = User.total_users()
            total_attendees = Attendee.total_conference_attendees(conference=conference)
            
            """
                Abstracts and attendee stats
                1. Total abstracts
                2. total paid abstracts
                3. Total unpaid abstracts
                4. Total approved abstracts
                5. Total attendee requests counting from payment
            """
            total_abstracts, total_paid_abstracts, total_unpaid_abstracts, total_approved_abstracts = Abstract.abstract_stats(main_theme=theme)
            total_payments, total_join_requests, total_pending_join_requests, total_abstract_payments = Payment.conference_payment_stats(conference=conference)
            
            stats = {
                "conference": {
                    "conference_name": conference.conference_name,
                    "start_date": conference.start_date,
                    "end_date": conference.end_date,
                    "capacity": conference.capacity,
                    "venue": conference.venue_name,
                    "total_sub_themes": total_sub_theme,
                    "total_target_groups": total_conference_target_groups,
                },
                "attendees": {
                    "total_users": total_users,
                    "total_attendees": total_attendees,
                },
                "abstracts": {
                    "total_abstracts": total_abstracts,
                    "total_paid_abstracts": total_paid_abstracts,
                    "total_unpaid_abstracts": total_unpaid_abstracts,
                    "total_approved_abstracts": total_approved_abstracts,
                },
                "payments": {
                    "total_payments": total_payments,
                    "total_join_requests": total_join_requests,
                    "total_pending_join_requests": total_pending_join_requests,
                    "total_abstract_payments": total_abstract_payments,
                }
            }
            
            return Response(data={"stats": stats}, status=status.HTTP_200_OK)
            
            
        except Exception as e:
            logger.error(f"Unexpected error occured: {e}", exc_info=True)
            return Response(data={"detail", str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)