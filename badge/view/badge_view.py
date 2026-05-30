import logging

from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from conference.models import Conference
from badge.models import BadgeGenerationJob
from badge.tasks import generate_conference_badges_task
from badge.serializers import BadgeGenerationJobSerializer

from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission

logger = logging.getLogger(__name__)


class BadgeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        "generate_badges": AppPermissionEnum.CREATE_BADGE.value,
        "job_status": AppPermissionEnum.READ_BADGE.value,
        "download_badges": AppPermissionEnum.READ_BADGE.value,
        "cancel_job": AppPermissionEnum.DELETE_BADGE.value,
    }
    
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_job(self, request: Request, pk=None):
        """
        Cancels and deletes any active badge generation job for a conference.
        """

        try:
            conference = Conference.get_conference_by_id(pk)

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # --------------------------------------------------
            # HARD CANCEL (your existing logic)
            # --------------------------------------------------
            BadgeGenerationJob.kill_and_delete(conference)

            return Response(
                {
                    "detail": "Badge generation job cancelled and cleared",
                    "conference_id": conference.conference_id,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Failed to cancel badge job")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================
    # 1. GENERATE BADGES
    # =====================================================
    @action(detail=True, methods=["post"], url_path="generate")
    def generate_badges(self, request: Request, pk=None):

        try:
            conference = Conference.get_conference_by_id(pk)

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # HARD RESET (safe version should ideally CANCEL not delete)
            BadgeGenerationJob.kill_and_delete(conference)

            job = BadgeGenerationJob.objects.create(
                conference=conference,
                status=BadgeGenerationJob.Status.PENDING,
                started_at=timezone.now(),
            )

            async_result = generate_conference_badges_task.delay(str(job.job_id))

            job.task_id = async_result.id
            job.save(update_fields=["task_id"])

            return Response(
                BadgeGenerationJobSerializer({
                    "job_id": job.job_id,
                    "conference_id": conference.conference_id,
                    "conference_name": conference.conference_name,
                    "status": job.status,
                    "total_attendees": job.total_attendees,
                    "processed_attendees": job.processed_attendees,
                    "successful_badges": job.successful_badges,
                    "failed_badges": job.failed_badges,
                    "progress": 0.0,
                    "zip_file": None,
                    "started_at": job.started_at,
                    "completed_at": None,
                    "created_at": job.created_at,
                }).data,
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception as e:
            logger.exception("Failed to start badge generation")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================
    # 2. JOB STATUS (NOW BY CONFERENCE ID)
    # =====================================================
    @action(detail=True, methods=["get"], url_path="status")
    def job_status(self, request: Request, pk=None):

        try:
            job = (
                BadgeGenerationJob.objects
                .select_related("conference")
                .get(conference__conference_id=pk)
            )

            return Response(
                BadgeGenerationJobSerializer({
                    "job_id": job.job_id,
                    "conference_id": job.conference.conference_id,
                    "conference_name": job.conference.conference_name,
                    "status": job.status,
                    "total_attendees": job.total_attendees,
                    "processed_attendees": job.processed_attendees,
                    "successful_badges": job.successful_badges,
                    "failed_badges": job.failed_badges,
                    "progress": self._progress(job),
                    "zip_file": job.zip_file.url if job.zip_file else None,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "created_at": job.created_at,
                }).data,
                status=status.HTTP_200_OK,
            )

        except BadgeGenerationJob.DoesNotExist:
            return Response(
                {"detail": "No badge job found for this conference"},
                status=status.HTTP_404_NOT_FOUND,
            )

    # =====================================================
    # 3. DOWNLOAD (UNCHANGED LOGIC, but conference-driven is fine too)
    # =====================================================
    @action(detail=True, methods=["get"], url_path="download")
    def download_badges(self, request: Request, pk=None):
        print("download_badges called with conference_id:", pk)  # Debug log

        try:
            job = (
                BadgeGenerationJob.objects
                .select_related("conference")
                .get(conference__conference_id=pk)
            )

            if job.status != BadgeGenerationJob.Status.COMPLETED:
                return Response(
                    {
                        "detail": "Badges not ready yet",
                        "status": job.status,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not job.zip_file:
                raise Http404("ZIP file not found")

            file_handle = job.zip_file.open("rb")

            response = FileResponse(
                file_handle,
                content_type="application/zip"
            )

            response["Content-Disposition"] = (
                f'attachment; filename="badges_{job.conference.conference_name}.zip"'
            )

            return response

        except BadgeGenerationJob.DoesNotExist:
            return Response(
                {"detail": "No badge job found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    # =====================================================
    # 4. PROGRESS CALC
    # =====================================================
    def _progress(self, job: BadgeGenerationJob):
        if job.total_attendees == 0:
            return 0.0
        return round(
            (job.processed_attendees / job.total_attendees) * 100,
            2,
        )