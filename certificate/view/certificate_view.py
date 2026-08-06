import logging

from django.http import FileResponse, Http404
from django.utils import timezone
from certificate.tasks import generate_conference_certificates_task
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from certificate.models import CertificateZip, CertificateGenerationJob
from certificate.serializers import (
    CertificateGenerationJobSerializer,
    CertificateZipSerializer,
)
from conference.models import Conference
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission

logger = logging.getLogger(__name__)


class CertificateViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        "generate_certificates": AppPermissionEnum.CREATE_CERTIFICATE.value,
        "job_status": AppPermissionEnum.READ_CERTIFICATE.value,
        "download_certificates": AppPermissionEnum.READ_CERTIFICATE.value,
        "cancel_job": AppPermissionEnum.DELETE_CERTIFICATE.value,
        "list_zipped_certificates": AppPermissionEnum.READ_CERTIFICATE.value,
    }

    # =====================================================
    # 1. CANCEL JOB
    # Route: POST /api/v1/certificates/{conference_id}/cancel/
    # =====================================================
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_job(self, request: Request, pk=None):
        """
        Cancels and deletes any active certificate generation job for a conference.
        """
        try:
            conference = Conference.get_conference_by_id(pk)

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            CertificateGenerationJob.kill_and_delete(conference)

            return Response(
                {
                    "detail": "Certificate generation job cancelled and cleared",
                    "conference_id": conference.conference_id,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Failed to cancel certificate job")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================
    # 2. GENERATE CERTIFICATES
    # Route: POST /api/v1/certificates/{conference_id}/generate/
    # =====================================================
    @action(detail=True, methods=["post"], url_path="generate")
    def generate_certificates(self, request: Request, pk=None):
        try:
            conference = Conference.get_conference_by_id(pk)

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # HARD RESET
            CertificateGenerationJob.kill_and_delete(conference)

            job = CertificateGenerationJob.objects.create(
                conference=conference,
                status=CertificateGenerationJob.Status.PENDING,
                started_at=timezone.now(),
            )

            async_result = generate_conference_certificates_task.delay(str(job.job_id))

            job.task_id = async_result.id
            job.save(update_fields=["task_id"])

            return Response(
                CertificateGenerationJobSerializer({
                    "job_id": job.job_id,
                    "conference_id": conference.conference_id,
                    "conference_name": conference.conference_name,
                    "status": job.status,
                    "total_attendees": job.total_attendees,
                    "processed_attendees": job.processed_attendees,
                    "successful_certificates": job.successful_certificates,
                    "failed_certificates": job.failed_certificates,
                    "progress": 0.0,
                    "zip_file": None,
                    "started_at": job.started_at,
                    "completed_at": None,
                    "created_at": job.created_at,
                }).data,
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception as e:
            logger.exception("Failed to start certificate generation")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================
    # 3. JOB STATUS
    # Routes: 
    #   GET /api/v1/certificates/status/ (All active jobs)
    #   GET /api/v1/certificates/status/?conference_id=<id> (Specific conference)
    # =====================================================
    @action(detail=False, methods=["get"], url_path="status")
    def job_status(self, request: Request):
        conference_id = request.query_params.get("conference_id")

        # Base query: Exclude COMPLETED jobs so we only track active/pending work
        queryset = (
            CertificateGenerationJob.objects
            .select_related("conference")
            .exclude(status=CertificateGenerationJob.Status.COMPLETED)
        )

        # Filter by specific conference if passed
        if conference_id:
            queryset = queryset.filter(conference__conference_id=conference_id)

        # Order by newest first
        jobs = queryset.order_by("-created_at")

        # If asking for a specific conference and none found, return 404 (or empty list)
        if conference_id and not jobs.exists():
            return Response(
                {"detail": "No active certificate job found for this conference"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Serialize list of jobs
        data = [
            {
                "job_id": job.job_id,
                "conference_id": job.conference.conference_id,
                "conference_name": job.conference.conference_name,
                "status": job.status,
                "total_attendees": job.total_attendees,
                "processed_attendees": job.processed_attendees,
                "successful_certificates": job.successful_certificates,
                "failed_certificates": job.failed_certificates,
                "progress": self._progress(job),
                "zip_file": job.zip_file.url if job.zip_file else None,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "created_at": job.created_at,
            }
            for job in jobs
        ]

        return Response(
            CertificateGenerationJobSerializer(data, many=True).data,
            status=status.HTTP_200_OK,
        )

    # =====================================================
    # 4. DOWNLOAD ZIPPED CERTIFICATES
    # Route: GET /api/v1/certificates/{conference_id}/download/
    # =====================================================
    @action(detail=True, methods=["get"], url_path="download")
    def download_certificates(self, request: Request, pk=None):
        try:
            job = (
                CertificateGenerationJob.objects
                .select_related("conference")
                .get(conference__conference_id=pk)
            )

            if job.status != CertificateGenerationJob.Status.COMPLETED:
                return Response(
                    {
                        "detail": "Certificates not ready yet",
                        "status": job.status,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not job.zip_file:
                raise Http404("ZIP file not found")

            file_handle = job.zip_file.open("rb")

            response = FileResponse(
                file_handle,
                content_type="application/zip",
            )

            response["Content-Disposition"] = (
                f'attachment; filename="certificates_{job.conference.conference_name}.zip"'
            )

            return response

        except CertificateGenerationJob.DoesNotExist:
            return Response(
                {"detail": "No certificate job found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    # =====================================================
    # 5. PAGINATED LIST OF ALL ZIPPED CERTIFICATES (FOR FRONTEND TABLE)
    # Route: GET /api/v1/certificates/zips/
    # =====================================================
    @action(detail=False, methods=["get"], url_path="zips")
    def list_zipped_certificates(self, request: Request):
        try:
            zips = (
                CertificateZip.objects
                .select_related("conference")
                .exclude(zip_file="")
                .order_by("-updated_at")
            )

            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(zips, request)

            if page is not None:
                serializer = CertificateZipSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = CertificateZipSerializer(zips, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Error retrieving zipped certificates list")
            return Response(
                {"detail": "An error occurred while retrieving zipped certificates."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================
    # 6. PROGRESS CALC
    # =====================================================
    def _progress(self, job: CertificateGenerationJob):
        if job.total_attendees == 0:
            return 0.0
        return round(
            (job.processed_attendees / job.total_attendees) * 100,
            2,
        )