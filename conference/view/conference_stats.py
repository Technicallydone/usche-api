# src/conference/views.py
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from abstracts.models import Abstract
from attendee.models import Attendee
from conference.models import Conference, TargetGroup
from conference.serializers import ConferenceStatsSerializer
from payment.models import Payment
from themes.models import MainTheme, SubTheme
from user.enums.permission_enums import AppPermissionEnum
from user.models import User
from user.permissions import HasAppPermission

logger = logging.getLogger(__name__)

class ConferenceStatsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    
    permission_mapping = {
        'retrieve': AppPermissionEnum.READ_CONFERENCE_STATS.value,
    }

    def retrieve(self, request, pk=None):
        if not pk:
            return Response(
                {"detail": "Conference ID is mandatory"},
                status=status.HTTP_406_NOT_ACCEPTABLE
            )
        
        try:
            # Get conference
            conference = Conference.get_conference_by_id(conference_id=pk)
            if not conference:
                return Response(
                    {"detail": "No conference found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # -----------------------------
            # User statistics
            # -----------------------------
            attendance_stats = User.attendance_stats()
            registration_per_year_stats = User.registration_per_year_stats()
            recent_registration_stats = User.recent_registration_stats(days=7, limit=10)

            # -----------------------------
            # Payment statistics
            # -----------------------------
            total_payments, total_join_requests, total_pending_join_requests, total_abstract_payments = Payment.conference_payment_stats(conference=conference)
            payment_activity_stats = Payment.payment_activity_stats()

            # -----------------------------
            # Conference theme & targets
            # -----------------------------
            theme = MainTheme.get_theme_by_conference(conference)
            if not theme:
                return Response(
                    {"detail": f"No main theme found for {conference.conference_name}"},
                    status=status.HTTP_404_NOT_FOUND
                )

            total_sub_theme = SubTheme.get_total_theme_subthemes(theme=theme)
            total_conference_target_groups = TargetGroup.total_conference_target_groups(conference=conference)

            # -----------------------------
            # Attendee statistics
            # -----------------------------
            total_users = User.total_users()
            total_attendees = Attendee.total_conference_attendees(conference=conference)

            # -----------------------------
            # Abstract statistics
            # -----------------------------
            total_abstracts, total_paid_abstracts, total_unpaid_abstracts, total_approved_abstracts = Abstract.abstract_stats(main_theme=theme)

            # -----------------------------
            # Build stats dictionary
            # -----------------------------
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
                    "attendance_stats": attendance_stats,
                    "registration_per_year_stats": list(registration_per_year_stats),
                    "recent_registration_stats": [
                        {
                            "id": u.user_id,
                            "full_name": u.full_name,
                            "email": u.email,
                            "created_at": u.created_at
                        } for u in recent_registration_stats
                    ],
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
                    "payment_activity_stats": payment_activity_stats,
                }
            }

            serializer = ConferenceStatsSerializer(data=stats)
            serializer.is_valid(raise_exception=True)
            return Response({"stats": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )