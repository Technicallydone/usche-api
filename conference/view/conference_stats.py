import logging
from typing import cast
from django.http import   HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from abstracts.models import Abstract
from attendee.models import Attendee
from conference.models import Conference, TargetGroup
from payment.models import Payment
from theme.models import MainTheme, SubTheme
from user.models import User

logger = logging.getLogger(__name__)

class ConferenceStatsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated,]
  
    @action(detail=False, methods=['get'])
    def statisticts(self, request: HttpRequest):
        conference_id = request.GET.get('conference_id')
        
        
        if not conference_id:
            return Response({"detail": "Conference ID is mandatory"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        
        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            
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