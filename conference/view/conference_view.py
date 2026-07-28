import mimetypes
import os
import re
from django.http import FileResponse
import conference
from conference.utils.schedule_pdf import generate_schedule_pdf
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from abstracts.enums.abstract_status import AbstractStatus
from abstracts.models import Abstract
from attendee.models import Attendee
from conference.models import BankAccount
from conference.models import (
    ConferenceSchedule,
    TargetGroup,
    RegistrationFee,
    ScheduleDay,
    Conference,
    ConferenceSlider,
    PreConferenceSlider
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from conference.serializers import (
    ConferenceSerializer,
    ConferenceDetailSerializer,
    CreateConferenceSerializer,
    CreateVenueSerializer,
    CreateRegistrationFeeSerializer,
    CreateTargetGroupSerializer,
    CreateBankAccountSerializer,
    CreateScheduleDaySerializer,
    CreateConferenceScheduleSerializer,
    ConferenceStatsSerializer,
    UpdateConferenceSerializer,
    SVGUploadSerializer,
    SliderBulkUploadSerializer
)
from payment.model.payment import Payment
from themes.models import MainTheme, SubTheme
from usche_app import settings
from user.enums.permission_enums import AppPermissionEnum
from user.model.user_model import User
from user.permissions import HasAppPermission
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from datetime import timedelta
import logging
from django.utils import timezone
from django.db.models import Count, Q

from utils.qr_code_generator import generate_qr_code

logger = logging.getLogger(__name__)

class ConferenceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny, HasAppPermission]
    
    permission_mapping = {
        'list': AppPermissionEnum.READ_CONFERENCE.value,
        # 'retrieve': AppPermissionEnum.READ_CONFERENCE.value,
        'retrieve_certificat_template': AppPermissionEnum.READ_CONFERENCE.value,
        'retrieve_id_badge_template': AppPermissionEnum.READ_CONFERENCE.value,
        'create': AppPermissionEnum.CREATE_CONFERENCE.value,
        'create_venue': AppPermissionEnum.UPDATE_CONFERENCE.value,
        'create_registration_fee': AppPermissionEnum.CREATE_CONFERENCE.value,
        'create_target_group': AppPermissionEnum.CREATE_CONFERENCE.value,
        'create_bank_account': AppPermissionEnum.CREATE_CONFERENCE.value,
        'create_schedule_day': AppPermissionEnum.CREATE_CONFERENCE.value,
        'create_conference_schedule': AppPermissionEnum.CREATE_CONFERENCE.value,
        'stats': AppPermissionEnum.READ_CONFERENCE_STATS.value,
        'update_id_badge_background': AppPermissionEnum.UPDATE_CONFERENCE.value,
        'update_certificate_background': AppPermissionEnum.UPDATE_CONFERENCE.value,
        'update': AppPermissionEnum.UPDATE_CONFERENCE.value,
        'update_venue': AppPermissionEnum.UPDATE_CONFERENCE.value,
        'upload_conference_sliders': AppPermissionEnum.CREATE_CONFERENCE.value,
        'toggle_conference_slider': AppPermissionEnum.UPDATE_CONFERENCE.value,
        'toggle_pre_conference_slider': AppPermissionEnum.UPDATE_CONFERENCE.value
    }
    
    @action(
        detail=True,
        methods=["get"],
        url_path="schedule/pdf",
    )
    def export_schedule_pdf(self, request, pk=None):

        try:
            conference = (
                Conference.objects
                .prefetch_related(
                    "schedule_days__schedules"
                )
                .get(
                    conference_id=pk
                )
            )


            pdf = generate_schedule_pdf(
                conference
            )


            filename = (
                f"{conference.conference_name}"
                "-schedule.pdf"
            )


            return FileResponse(
                pdf,
                as_attachment=True,
                filename=filename,
                content_type="application/pdf",
            )


        except Conference.DoesNotExist:

            return Response(
                {
                    "detail": "Conference not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )
    
    @action(
        detail=True,
        methods=["get"],
        url_path="qr-code",
    )
    def schedule_qr_code(self, request: Request, pk=None):
        download_url = (
            f"{settings.FRONTEND_BASE_URL}/conference/{pk}/schedule/export"
        )

        img_io = generate_qr_code(download_url)

        return FileResponse(
            img_io,
            content_type="image/png",
        )
    
    @action(detail=False, methods=["get"], url_path="list")
    def list_conferences(self, request: Request):
        try:
            conferences = Conference.objects.all().order_by("-listing_date")

            return Response(
                [
                    {
                        "conference_id": str(conf.conference_id),
                        "conference_name": conf.conference_name,
                        "year": conf.year
                    }
                    for conf in conferences
                ],
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Error fetching conferences: {e}",
                exc_info=True,
            )
            return Response(
                {"detail": "Failed to fetch conferences"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=['get'], url_path='sliders/(?P<slider_id>[^/.]+)')
    def retrieve_conference_slider(self, request: Request, slider_id=None):
        try:
            slider = ConferenceSlider.objects.get(id=slider_id)

            if not slider.image:
                return Response(
                    {"detail": "No image found for this slider"},
                    status=status.HTTP_404_NOT_FOUND
                )

            file_path = slider.image.path

            if not os.path.exists(file_path):
                return Response(
                    {"detail": "Slider image not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            content_type, _ = mimetypes.guess_type(file_path)

            return FileResponse(
                open(file_path, "rb"),
                content_type=content_type or "application/octet-stream"
            )

        except ConferenceSlider.DoesNotExist:
            return Response(
                {"detail": "Slider not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='pre-sliders/(?P<slider_id>[^/.]+)')
    def retrieve_pre_conference_slider(self, request: Request, slider_id=None):
        try:
            slider = PreConferenceSlider.objects.get(id=slider_id)

            if not slider.image:
                return Response(
                    {"detail": "No image found for this slider"},
                    status=status.HTTP_404_NOT_FOUND
                )

            file_path = slider.image.path

            if not os.path.exists(file_path):
                return Response(
                    {"detail": "Slider image not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            content_type, _ = mimetypes.guess_type(file_path)

            return FileResponse(
                open(file_path, "rb"),
                content_type=content_type or "application/octet-stream"
            )

        except PreConferenceSlider.DoesNotExist:
            return Response(
                {"detail": "Slider not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=["patch"], url_path="conference-sliders/toggle")
    def toggle_conference_slider(self, request, pk=None):
        try:
            slider = ConferenceSlider.objects.filter(pk=pk).first()

            if not slider:
                return Response({"detail": "Slider not found"}, status=404)

            new_state = slider.toggle_active()

            return Response({
                "id": str(slider.id),
                "is_active": new_state
            })

        except Exception as e:
            logger.error(f"Error toggling conference slider: {e}", exc_info=True)
            return Response(
                {"detail": "Failed to toggle slider"},
                status=500
            )
            
    @action(detail=True, methods=["patch"], url_path="pre-conference-sliders/toggle")
    def toggle_pre_conference_slider(self, request, pk=None):
        try:
            slider = PreConferenceSlider.objects.filter(pk=pk).first()

            if not slider:
                return Response({"detail": "Slider not found"}, status=404)

            new_state = slider.toggle_active()

            return Response({
                "id": str(slider.id),
                "is_active": new_state
            })

        except Exception as e:
            logger.error(f"Error toggling pre-conference slider: {e}", exc_info=True)
            return Response(
                {"detail": "Failed to toggle slider"},
                status=500
            )
    
    @action(detail=False, methods=["post"], url_path="pre-conference-sliders")
    def upload_pre_conference_sliders(self, request: Request):
        try:
            serializer = SliderBulkUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            conference_id = serializer.validated_data["conference_id"]
            images = serializer.validated_data["images"]

            conference = Conference.objects.filter(
                conference_id=conference_id
            ).first()

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            for img in images:
                PreConferenceSlider.objects.create(
                    conference=conference,
                    image=img
                )

            return Response(
                {"detail": "Pre conference sliders created successfully"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error uploading pre-conference sliders: {e}", exc_info=True)
            return Response(
                {"detail": "Failed to upload pre-conference sliders"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=["post"], url_path="conference-sliders")
    def upload_conference_sliders(self, request: Request):
        try:
            serializer = SliderBulkUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            conference_id = serializer.validated_data.get('conference_id')
            images = serializer.validated_data.get('images')

            conference = Conference.objects.filter(
                conference_id=conference_id
            ).first()

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            for img in images:
                ConferenceSlider.objects.create(
                    conference=conference,
                    image=img
                )

            return Response(data={"detail": "Conference sliders created successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error uploading conference sliders: {e}", exc_info=True)
            return Response(
                {"detail": "Failed to upload conference sliders"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='open')
    def open_submission(self, request: Request):
        try:
            now = timezone.now()

            conferences = Conference.objects.filter(
                end_date__gte=now.date(),
            ).filter(
                Q(
                    abstract_submission_open=True,
                    abstract_submission_deadline__gt=now,
                )
                |
                Q(
                    attendee_registration_open=True,
                    attendee_registration_deadline__gt=now,
                )
            ).order_by("-listing_date")

            serializer = ConferenceDetailSerializer(
                conferences,
                many=True
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"Error fetching open conferences: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request: Request):
        try:
            now = timezone.now()
            last_7_days = now - timedelta(days=7)

            # -----------------------------------
            # CONFERENCE STATS
            # -----------------------------------
            total_conferences = Conference.objects.count()

            active_conferences = Conference.objects.filter(
                end_date__gte=now.date()
            ).count()

            # -----------------------------------
            # USER & ATTENDEE STATS
            # -----------------------------------
            total_users = User.objects.count()

            total_attendees = Attendee.objects.count()

            recent_users = User.objects.filter(
                created_at__gte=last_7_days
            ).order_by('-created_at')[:10]

            # registrations per year (FROM ATTENDEES)
            registrations_per_year = (
                Attendee.objects
                .values('conference__year')
                .annotate(count=Count('attendee_id'))
                .order_by('conference__year')
            )

            # -----------------------------------
            # ABSTRACT STATS
            # -----------------------------------
            total_abstracts = Abstract.objects.count()

            total_paid_abstracts = Abstract.objects.filter(
                is_payment_done=True
            ).count()

            total_unpaid_abstracts = Abstract.objects.filter(
                is_payment_done=False
            ).count()

            total_approved_abstracts = Abstract.objects.filter(
                status=AbstractStatus.APPROVED.value
            ).count()

            # -----------------------------------
            # PAYMENT STATS
            # -----------------------------------
            payment_qs = Payment.objects.all()

            payment_aggregate = payment_qs.aggregate(
                total_transactions=Count('payment_id')
            )

            total_amount = 0
            currency_summary = {}

            for payment in payment_qs:
                value = payment.amount.strip().upper()

                match = re.match(
                    r"^(\d+(\.\d{1,2})?)\s?([A-Z]{3})$",
                    value
                )

                if match:
                    amount = float(match.group(1))
                    currency = match.group(3)

                    total_amount += amount

                    currency_summary[currency] = (
                        currency_summary.get(currency, 0) + amount
                    )

            recent_payments = Payment.objects.filter(
                timestamp__gte=last_7_days
            ).count()

            # -----------------------------------
            # THEMES & TARGET GROUPS
            # -----------------------------------
            total_main_themes = MainTheme.objects.count()

            total_sub_themes = SubTheme.objects.count()

            total_target_groups = TargetGroup.objects.count()

            # -----------------------------------
            # TOP CONFERENCES (by attendees)
            # -----------------------------------
            top_conferences = (
                Attendee.objects
                .values(
                    'conference__conference_id',
                    'conference__conference_name',
                )
                .annotate(
                    total_attendees=Count('attendee_id')
                )
                .order_by('-total_attendees')[:5]
            )

            # -----------------------------------
            # RESPONSE STRUCTURE
            # -----------------------------------
            data = {
                "overview": {
                    "total_conferences": total_conferences,
                    "active_conferences": active_conferences,
                    "total_users": total_users,
                    "total_attendees": total_attendees,
                },

                "abstracts": {
                    "total": total_abstracts,
                    "paid": total_paid_abstracts,
                    "unpaid": total_unpaid_abstracts,
                    "approved": total_approved_abstracts,
                },

                "payments": {
                    "total_amount": total_amount,
                    "currency_summary": currency_summary,
                    "total_transactions": (
                        payment_aggregate.get("total_transactions") or 0
                    ),
                    "last_7_days": recent_payments,
                },

                "themes": {
                    "total_main_themes": total_main_themes,
                    "total_sub_themes": total_sub_themes,
                    "total_target_groups": total_target_groups,
                },

                "trends": {
                    "registrations_per_year": [
                        {
                            "year": item["conference__year"],
                            "count": item["count"]
                        }
                        for item in registrations_per_year
                    ],

                    "recent_users": [
                        {
                            "id": u.user_id,
                            "full_name": (
                                f"{u.first_name or ''} "
                                f"{u.last_name or ''}"
                            ).strip(),
                            "email": u.email,
                            "created_at": u.created_at,
                        }
                        for u in recent_users
                    ],
                },

                "top_conferences": list(top_conferences),
            }

            serializer = ConferenceStatsSerializer(data=data)

            serializer.is_valid(raise_exception=True)

            return Response(
                {"stats": serializer.data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"Unexpected error occurred: {e}",
                exc_info=True
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=False, methods=['post'], url_path='venue/update')
    def update_venue(self, request: Request):
        serializer = CreateVenueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        try:
            conference = Conference.get_conference_by_id(
                conference_id=validated_data.get("conference_id")
            )

            if conference is None:
                return Response(
                    data={"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            conference.venue_name = validated_data.get("venue_name")
            conference.venue_website = validated_data.get("venue_website")
            conference.venue_description = validated_data.get("venue_description")
            conference.venue_directions = validated_data.get("venue_directions")

            conference.save(
                update_fields=[
                    "venue_name",
                    "venue_website",
                    "venue_description",
                    "venue_directions",
                ]
            )

            return Response(
                data={
                    "detail": "Venue updated successfully",
                    "id": conference.conference_id,
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=['post'], url_path='venue/create')
    def create_venue(self, request: Request):
        serializer = CreateVenueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        try:
            conference = Conference.get_conference_by_id(conference_id=validated_data.get('conference_id'))
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            conference.venue_name = validated_data.get('venue_name')
            conference.venue_website = validated_data.get('venue_website')
            conference.venue_description = validated_data.get('venue_description')
            conference.venue_directions = validated_data.get('venue_directions')
            
            conference.save(update_fields=['venue_name', 'venue_website', 'venue_description', 'venue_directions'])
            
            return Response({"detail": "Venue created", "id": conference.conference_id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='registration-fee/create')
    def create_registration_fee(self, request: Request):
        serializer = CreateRegistrationFeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            conference = Conference.get_conference_by_id(conference_id=validated_data.get('conference_id'))
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            fee = RegistrationFee.objects.create(
                conference=conference,
                category=validated_data.get('category'),
                early_bird_fee=validated_data.get('early_bird_fee'),
                late_registration_fee=validated_data.get('late_registration_fee'),
            )
            return Response({"detail": "Registration fee created", "id": fee.fee_id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='target-group/create')
    def create_target_group(self, request: Request):
        serializer = CreateTargetGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            conference = Conference.get_conference_by_id(conference_id=validated_data.get('conference_id'))
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            group = TargetGroup.objects.create(
                conference=conference,
                group_name=validated_data.get('group_name'),
            )
            return Response({"detail": "Target group created", "id": group.group_id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='bank-account/create')
    def create_bank_account(self, request: Request):
        serializer = CreateBankAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            conference = Conference.get_conference_by_id(conference_id=validated_data.get('conference_id'))
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            account = BankAccount.objects.create(
                conference=conference,
                account_name=validated_data.get('account_name'),
                account_number=validated_data.get('account_number'),
                bank_name=validated_data.get('bank_name'),
                currency=validated_data.get('currency'),
                bank_code=validated_data.get('bank_code'),
                swift_code=validated_data.get('swift_code'),
            )
            return Response({"detail": "Bank account created", "id": account.account_id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='schedule-day/create')
    def create_schedule_day(self, request: Request):
        serializer = CreateScheduleDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            conference = Conference.get_conference_by_id(conference_id=validated_data.get('conference_id'))
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            day = ScheduleDay.objects.create(
                conference=conference,
                date=validated_data.get('date'),
                title=validated_data.get('title'),
                location=validated_data.get('location'),
            )
            return Response({"detail": "Schedule day created", "id": day.schedule_day_id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='conference-schedule/create')
    def create_conference_schedule(self, request: Request):
        serializer = CreateConferenceScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            schedule_day = ScheduleDay.get_by_id(schedule_day_id=validated_data.get('schedule_day_id'))
            
            if schedule_day is None:
                return Response(data={"detail": "Scheduled day not found"}, status=status.HTTP_404_NOT_FOUND)
            
            schedule = ConferenceSchedule.objects.create(
                schedule_day=schedule_day,
                date=validated_data.get('date'),
                start_time=validated_data.get('start_time'),
                end_time=validated_data.get('end_time'),
                activity=validated_data.get('activity'),
                speaker=validated_data.get('speaker'),
                moderator=validated_data.get('moderator'),
                hall=validated_data.get('hall'),
                session_type=validated_data.get('session_type'),
            )
            return Response({"detail": "Conference schedule created", "id": schedule.id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    
    def create(self, request: Request):
        serializer = CreateConferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        try:
            conference = Conference.objects.create(
                conference_name=validated_data.get("conference_name"),
                description=validated_data.get("description"),
                start_date=validated_data.get("start_date"),
                end_date=validated_data.get("end_date"),
                start_time=validated_data.get("start_time"),
                end_time=validated_data.get("end_time"),
                capacity=validated_data.get("capacity"),

                abstract_submission_open=validated_data.get(
                    "abstract_submission_open",
                    False,
                ),
                abstract_submission_deadline=validated_data.get(
                    "abstract_submission_deadline"
                ),

                attendee_registration_open=validated_data.get(
                    "attendee_registration_open",
                    False,
                ),
                attendee_registration_deadline=validated_data.get(
                    "attendee_registration_deadline"
                ),

                year=validated_data.get("year"),

                certificate_background=validated_data.get(
                    "certificate_background"
                ),
                id_badge_background=validated_data.get(
                    "id_badge_background"
                ),
            )
            
            return Response(
                data={"detail": "Conference created successfully", "id": conference.conference_id},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request: Request, pk=None):
        serializer = UpdateConferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        try:
            conference = Conference.objects.get(conference_id=pk)

            conference.conference_name = validated_data.get("conference_name")
            conference.description = validated_data.get("description")
            conference.start_date = validated_data.get("start_date")
            conference.end_date = validated_data.get("end_date")
            conference.start_time = validated_data.get("start_time")
            conference.end_time = validated_data.get("end_time")
            conference.capacity = validated_data.get("capacity")

            conference.abstract_submission_open = validated_data.get(
                "abstract_submission_open"
            )
            conference.abstract_submission_deadline = validated_data.get(
                "abstract_submission_deadline"
            )

            conference.attendee_registration_open = validated_data.get(
                "attendee_registration_open"
            )
            conference.attendee_registration_deadline = validated_data.get(
                "attendee_registration_deadline"
            )

            conference.year = validated_data.get("year")

            conference.save()

            return Response(
                data={
                    "detail": "Conference updated successfully",
                    "id": conference.conference_id,
                },
                status=status.HTTP_200_OK,
            )

        except Conference.DoesNotExist:
            return Response(
                data={"detail": "Conference not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError as e:
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
    @action(detail=True, methods=["post"], url_path="certificate-background")
    def update_certificate_background(self, request, pk=None):
        serializer = SVGUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]

        try:
            conference = Conference.objects.get(pk=pk)

            if conference.certificate_background:
                old_path = conference.certificate_background.path
                if os.path.isfile(old_path):
                    os.remove(old_path)

            conference.certificate_background = file
            conference.save(update_fields=["certificate_background"])

            return Response(
                {
                    "detail": "Certificate background updated successfully",
                    "id": conference.conference_id,
                },
                status=status.HTTP_200_OK,
            )

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
            
    @action(detail=True, methods=["post"], url_path="id-badge-background")
    def update_id_badge_background(self, request, pk=None):
        serializer = SVGUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]

        try:
            conference = Conference.objects.get(pk=pk)

            # Delete the previous file
            if conference.id_badge_background:
                conference.id_badge_background.delete(save=False)

            # Save the new one
            conference.id_badge_background = file
            conference.save(update_fields=["id_badge_background"])

            return Response(
                {
                    "detail": "ID badge background updated successfully",
                    "id": conference.conference_id,
                },
                status=status.HTTP_200_OK,
            )

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
            
    @action(detail=True, methods=['get'], url_path='badge-template')
    def retrieve_id_badge_template(self, request: Request, pk=None):
        if pk is None:
            return Response(
                {"detail": "No conference ID provided"},
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:
            conference = Conference.objects.get(conference_id=pk)

            if not conference.certificate_background:
                return Response(
                    {"detail": "No id badge template uploaded"},
                    status=status.HTTP_404_NOT_FOUND
                )

            file_path = conference.id_badge_background.path

            if not os.path.exists(file_path):
                return Response(
                    {"detail": "Id badge template not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            content_type, _ = mimetypes.guess_type(file_path)

            return FileResponse(
                open(file_path, 'rb'),
                content_type=content_type or 'application/octet-stream'
            )

        except Conference.DoesNotExist:
            logger.error(f"Conference with id {pk} not found.")
            return Response(
                {"detail": "Conference not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"Error while retrieving id badge certificate template: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='certificate-template')
    def retrieve_certificat_template(self, request: Request, pk=None):
        if pk is None:
            return Response(
                {"detail": "No conference ID provided"},
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:
            conference = Conference.objects.get(conference_id=pk)

            if not conference.certificate_background:
                return Response(
                    {"detail": "No certificate template uploaded"},
                    status=status.HTTP_404_NOT_FOUND
                )

            file_path = conference.certificate_background.path

            if not os.path.exists(file_path):
                return Response(
                    {"detail": "Certificate template not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            content_type, _ = mimetypes.guess_type(file_path)

            return FileResponse(
                open(file_path, 'rb'),
                content_type=content_type or 'application/octet-stream'
            )

        except Conference.DoesNotExist:
            logger.error(f"Conference with id {pk} not found.")
            return Response(
                {"detail": "Conference not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"Error while retrieving conference certificate template: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request: Request):
        """List conferences with pagination and order by listing_date descending"""
        

        try:
            conferences = Conference.objects.all().order_by('-listing_date')

            paginator = PageNumberPagination()
            paginator.page_size_query_param = 'page_size'
            page = paginator.paginate_queryset(conferences, request)

            if page is not None:
                serializer = ConferenceSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = ConferenceSerializer(conferences, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching conferences: {str(e)}")
            return Response({"detail": "Error fetching conferences"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request: Request, pk=None):
        """
        Retrieve a single conference by its primary key (conference_id)
        using the standard DRF retrieve method.
        """
        try:
            conference = (
            Conference.objects
                .filter(conference_id=pk)
                .select_related("theme")
                .prefetch_related(
                    "pre_conference_sliders",
                    "slider_images",
                    "sponsors",
                    "speakers",
                    "registration_fees",
                    "schedule_days",
                    "bank_accounts",
                    "groups",
                )
                .first()
            )
            
            if not conference:
                return Response({"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = ConferenceDetailSerializer(conference)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving conference {pk}: {str(e)}")
            return Response({"detail": "Error retrieving conference"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["get"], url_path="by-year")
    def retrieve_by_year(self, request: Request):
        year = request.query_params.get("year")
        
        if not year:
            return Response(
                {"detail": "Year is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conference = (
            Conference.objects
            .filter(year=year)
            .select_related("theme")
            .prefetch_related(
                "pre_conference_sliders",
                "slider_images",
                "sponsors",
                "speakers",
                "registration_fees",
                "schedule_days",
                "bank_accounts",
                "groups",
            )
            .first()
        )

        if not conference:
            return Response(
                {"detail": "Conference not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ConferenceDetailSerializer(conference)
        return Response(serializer.data)