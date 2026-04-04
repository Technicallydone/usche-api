from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.request import Request
from conference.models import Conference, ConferenceScheduleDocument
from conference.serializers import ConferenceDetailSerializer
from django.http import FileResponse, Http404
from utils.qr_code_generator import generate_qr_code
from usche_app import settings
from rest_framework.decorators import action

class ConferenceInfoViewSet(viewsets.ViewSet):
    """Endpoints to fetch conference information"""
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def read(self, request: Request):
        year = request.GET.get('year')
        
        try:
            conference = Conference.get_conference(year=year)
            if not conference:
                return Response({"detail": "No conference available"}, status=status.HTTP_404_NOT_FOUND)

            serializer = ConferenceDetailSerializer(conference)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="schedule/(?P<conference_id>[^/.]+)/download-pdf")
    def download_schedule_pdf(self, request: Request, conference_id=None):
        try:
            document = ConferenceScheduleDocument.objects.filter(
                conference__conference_id=conference_id,
                is_active=True
            ).first()
            if not document or not document.file:
                raise Http404("No active PDF found for this conference.")

            return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.title + ".pdf")
        except ConferenceScheduleDocument.DoesNotExist:
            raise Http404("PDF not found.")

    @action(detail=False, methods=["get"], url_path="schedule/(?P<conference_id>[^/.]+)/qr-code")
    def schedule_qr_code(self, request: Request, conference_id=None):
        download_url = f"{settings.FRONTEND_BASE_URL}/conference/schedule/{conference_id}/download"
        img_io = generate_qr_code(download_url)
        return FileResponse(img_io, content_type='image/png')