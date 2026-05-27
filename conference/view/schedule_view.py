import logging
from typing import Any, Dict, List

from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from conference.model.conference import Conference
from conference.model.conference_schedule import ConferenceSchedule
from conference.model.schedule_day import ScheduleDay

from conference.serializers import (
    CreateConferenceScheduleSerializer,
    CreateScheduleDaySerializer,
    UpdateConferenceScheduleSerializer,
    UpdateScheduleDaySerializer,
)

from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission

logger = logging.getLogger(__name__)


class ScheduleViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        "create_schedule_day": AppPermissionEnum.CREATE_SCHEDULE.value,
        "update_schedule_day": AppPermissionEnum.UPDATE_SCHEDULE.value,
        "bulk_update_days": AppPermissionEnum.UPDATE_SCHEDULE.value,
        "delete_schedule_day": AppPermissionEnum.DELETE_SCHEDULE.value,
        "create_conference_schedule": AppPermissionEnum.CREATE_SCHEDULE.value,
        "update_conference_schedule": AppPermissionEnum.UPDATE_SCHEDULE.value,
    }

    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def extract_schedule_days_from_request(data):
        items = []
        index = 0

        while data.get(f"schedule_days[{index}][schedule_day_id]") is not None:
            items.append({
                "schedule_day_id": data.get(f"schedule_days[{index}][schedule_day_id]"),
                "date": data.get(f"schedule_days[{index}][date]"),
                "title": data.get(f"schedule_days[{index}][title]"),
                "location": data.get(f"schedule_days[{index}][location]"),
            })
            index += 1

        return items

    # =====================================================
    # SCHEDULE DAY
    # =====================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="create-schedule",
    )
    def create_schedule_day(self, request: Request):
        serializer = CreateScheduleDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            conference = Conference.get_conference_by_id(
                data["conference_id"]
            )

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            day = ScheduleDay.objects.create(
                conference=conference,
                date=data["date"],
                title=data["title"],
                location=data.get("location", ""),
            )

            return Response(
                {
                    "detail": "Schedule day created",
                    "id": str(day.schedule_day_id),
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception("Failed to create schedule day")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["put"],
        url_path="update-schedule/(?P<day_id>[^/.]+)",
    )
    def update_schedule_day(
        self,
        request: Request,
        day_id=None,
    ):
        serializer = UpdateScheduleDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            day = ScheduleDay.objects.get(schedule_day_id=day_id)

            for field, value in data.items():
                setattr(day, field, value)

            day.save()

            return Response(
                {
                    "detail": "Schedule day updated",
                    "id": str(day.schedule_day_id),
                },
                status=status.HTTP_200_OK,
            )

        except ScheduleDay.DoesNotExist:
            return Response(
                {"detail": "Schedule day not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.exception("Failed to update schedule day")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["put"],
        url_path="bulk-update-days",
    )
    def bulk_update_days(self, request: Request):
        try:
            raw_days = self.extract_schedule_days_from_request(
                request.data
            )

            serializer = UpdateScheduleDaySerializer(
                data=raw_days,
                many=True,
            )

            serializer.is_valid(raise_exception=True)

            validated = serializer.validated_data

            updated_ids = []

            with transaction.atomic():
                for item in validated:
                    day = (
                        ScheduleDay.objects.select_for_update()
                        .filter(
                            schedule_day_id=item["schedule_day_id"]
                        )
                        .first()
                    )

                    if not day:
                        continue

                    day.title = item.get("title", day.title)
                    day.date = item.get("date", day.date)
                    day.location = item.get(
                        "location",
                        day.location,
                    )

                    day.save()

                    updated_ids.append(
                        str(day.schedule_day_id)
                    )

            return Response(
                {
                    "detail": "Schedule days updated",
                    "updated_ids": updated_ids,
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response(
                {"detail": e.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception(
                "Bulk update schedule days failed"
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["delete"],
        url_path="delete-day/(?P<day_id>[^/.]+)",
    )
    def delete_day(
        self,
        request: Request,
        day_id=None,
    ):
        try:
            day = ScheduleDay.objects.get(
                schedule_day_id=day_id
            )

            day.delete()

            return Response(
                {
                    "detail": "Schedule day deleted",
                    "id": day_id,
                },
                status=status.HTTP_200_OK,
            )

        except ScheduleDay.DoesNotExist:
            return Response(
                {"detail": "Schedule day not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.exception(
                "Delete schedule day failed"
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================
    # CONFERENCE SCHEDULE
    # =====================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="create-conference-schedule",
    )
    def create_conference_schedule(
        self,
        request: Request,
    ):
        serializer = CreateConferenceScheduleSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            day = ScheduleDay.objects.get(
                schedule_day_id=data["schedule_day_id"]
            )

            schedule = ConferenceSchedule.objects.create(
                schedule_day=day,
                date=data["date"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                activity=data.get("activity", ""),
                speaker=data.get("speaker", ""),
                moderator=data.get("moderator", ""),
                hall=data.get("hall", ""),
                session_type=data.get("session_type"),
            )

            return Response(
                {
                    "detail": "Conference schedule created",
                    "id": str(schedule.schedule_id),
                },
                status=status.HTTP_201_CREATED,
            )

        except ScheduleDay.DoesNotExist:
            return Response(
                {"detail": "Schedule day not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError as e:
            return Response(
                {"detail": e.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception(
                "Create conference schedule failed"
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["put"],
        url_path="update-conference-schedule/(?P<schedule_id>[^/.]+)",
    )
    def update_conference_schedule(
        self,
        request: Request,
        schedule_id=None,
    ):
        serializer = UpdateConferenceScheduleSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            schedule = ConferenceSchedule.objects.get(
                schedule_id=schedule_id
            )

            for field, value in data.items():
                setattr(schedule, field, value)

            schedule.save()

            return Response(
                {
                    "detail": "Conference schedule updated",
                    "id": str(schedule.schedule_id),
                },
                status=status.HTTP_200_OK,
            )

        except ConferenceSchedule.DoesNotExist:
            return Response(
                {"detail": "Conference schedule not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.exception(
                "Update conference schedule failed"
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )