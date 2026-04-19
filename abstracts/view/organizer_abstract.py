import logging
from typing import cast
from django.http import  HttpRequest
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from abstracts.enums.abstract_status import AbstractStatus
from abstracts.models import Abstract
from abstracts.serializers import AbstractSerializer, AbstractStatusUpdateSerializer, QRCodeVerificationSerializer, PaidAbstractSerializer
from attendee.model.attendee import Attendee
from conference.models import Conference
from services.email.tasks import send_email_task
from themes.models import MainTheme
from django.db import transaction
from rest_framework.pagination import PageNumberPagination

from usche_app import settings
from user.models import User


logger = logging.getLogger(__name__)

class OrganizerAbstractViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated,]
    
    @action(detail=False, methods=['post'])
    def retrieve_abstract_info(self, request: HttpRequest):
            
        conference_id = request.GET.get("conference_id")
        if not conference_id:
            return Response(
                data={"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            
        abstract_id = request.GET.get("abstract_id")
        if not abstract_id:
            return Response(
                data={"detail": "Abstract ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )


        try:
            abstract = Abstract.retrieve_abstract(abstract_id=abstract_id)
            
            
            if abstract is None:
                return Response(data={"detail": "Abstract not found"}, status=status.HTTP_404_NOT_FOUND)
            
            response_serializer = AbstractSerializer(abstract)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Abstract.MultipleObjectsReturned:
            logger.error(f"multiple abstracts.")
            return Response(
                {"detail": "Multiple abstracts found. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error(f"Error while retrieving abstract: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def verify_qr_code(self, request: HttpRequest):
        serializer = QRCodeVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        qr_data = serializer.validated_data["qr_data"]

        try:
            data_parts = dict(part.split(":") for part in qr_data.split(","))
            attendee_id = data_parts.get("ID")

            attendee = Attendee.get_attendee_by_id(attendee_id=attendee_id)
            
            attendee.update_status_to_attended()

            return Response({
                "detail": f"{attendee.participant.title} {attendee.participant.last_name} authenticated for {attendee.conference.conference_name}."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"QR Code verification failed: {str(e)}")
            return Response({"detail": "User or Conference not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def approve_abstract(self, request: HttpRequest):
        """Mark an abstract as approved."""

        serializer = AbstractStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        abstract_id = serializer.validated_data.get("abstract_id")
        comment = serializer.validated_data.get("comment")

        try:
            with transaction.atomic():

                abstract = Abstract.mark_as_approved(
                    abstract_id=abstract_id,
                    comment=comment
                )

                if not abstract:
                    return Response(
                        {"detail": "Abstract not found or already processed."},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Send approval email AFTER transaction succeeds
            send_email_task.delay(
                subject="Abstract Approved - USChE Conference",
                to=abstract.user.email,
                greeting=f"Hello {abstract.user.first_name},",
                lines=[
                    "Congratulations! Your submitted abstract has been approved.",
                    "You may now proceed with the conference payment process.",
                    f"Comment: {comment}" if comment else "We look forward to your participation."
                ],
                salutations=["Best regards,", "The USChE Organizing Committee"],
                button_text="Proceed to Payment",
                button_url=f"{settings.FRONTEND_BASE_URL}/dashboard",
                footer_text="© 2026 USChE - University of Dodoma"
            )

            return Response(
                {"detail": "Abstract approved successfully and user notified."},
                status=status.HTTP_200_OK
            )

        except Exception:
            logger.exception("Error while approving abstract.")
            return Response(
                {"detail": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def reject(self, request: HttpRequest):
        """Reject an abstract with an optional comment."""
        serializer = AbstractStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        abstract_id = serializer.validated_data["abstract_id"]
        comment = serializer.validated_data.get("comment")

        try:
            with transaction.atomic():

                abstract = Abstract.mark_as_rejected(
                    abstract_id=abstract_id,
                    comment=comment
                )

                if not abstract:
                    return Response(
                        {"detail": "Abstract not found or already processed."},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Send rejection email AFTER transaction succeeds
            send_email_task.delay(
                subject="Abstract Rejected - USChE Conference",
                to=abstract.user.email,
                greeting=f"Hello {abstract.user.first_name},",
                lines=[
                    "We regret to inform you that your submitted abstract has been rejected.",
                    f"Reason: {comment or 'No specific reason was provided.'}",
                    "You may review the feedback and submit a revised abstract if allowed."
                ],
                salutations=["Best regards,", "The USChE Organizing Committee"],
                button_text="View Submission",
                button_url=f"{settings.FRONTEND_BASE_URL}/dashboard",
                footer_text="© 2026 USChE - University of Dodoma"
            )

            return Response(
                {"detail": "Abstract rejected successfully and user notified."},
                status=status.HTTP_200_OK
            )

        except Exception:
            logger.exception("Error while rejecting abstract.")
            return Response(
                {"detail": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def filtered_abstracts(self, request: HttpRequest):
        user = cast(User, request.user)
            
        conference_id = request.GET.get("conference_id")
        search_query = request.GET.get("search_query")
        status_param = request.GET.get("status") 
        
        if not conference_id:
            return Response(
                {"detail": "Conference ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            conference = Conference.get_conference_by_id(conference_id=conference_id)
            if conference is None:
                return Response({"detail": "Conference not found."}, status=status.HTTP_404_NOT_FOUND)

            main_theme = MainTheme.get_theme_by_conference(conference=conference)
            if main_theme is None:
                return Response({"detail": "Conference has no main theme"}, status=status.HTTP_400_BAD_REQUEST)

            abstracts = Abstract.get_abstracts_by_status(
                main_theme=main_theme,
                status=status_param,
                search_query=search_query
            )

            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(abstracts, request)

            if page is not None:
                serializer = AbstractSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = AbstractSerializer(abstracts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error while retrieving abstracts for user {user.user_id}: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def conference_abstracts(self, request: HttpRequest):
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
            
            main_theme = MainTheme.get_theme_by_conference(conference=conference)
            
            if main_theme is None:
                return Response(data={"detail": "Conference have no main theme"}, status=status.HTTP_400_BAD_REQUEST)
            
            abstracts = Abstract.get_conference_abstracts(main_theme=main_theme, search_query=search_query)
            
            
            
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(abstracts, request)
            
            if page is not None:
                response_serializer = AbstractSerializer(page, many=True)
                return paginator.get_paginated_response(response_serializer.data)
            
            response_serializer = AbstractSerializer(abstracts, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error while retrieving abstracts {user.user_id}: {e}")
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
