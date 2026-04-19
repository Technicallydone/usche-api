import os
from django.http import FileResponse, Http404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
import logging

from conference.model.conference import Conference
from sponsors.models import Sponsor
from sponsors.serializers import CreateSponsorSerializer
from usche_app import settings
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission

logger = logging.getLogger(__name__)

class SponsorViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    
    permission_mapping = {
        'create': AppPermissionEnum.CREATE_SPONSOR.value,
    }

    def create(self, request: Request):
        serializer = CreateSponsorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            conference = Conference.get_conference_by_id(conference_id=validated_data.get('conference_id'))
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            sponsor = Sponsor.objects.create(
                conference=conference,
                name=validated_data.get('name'),
                logo=validated_data.get('logo'),
                website=validated_data.get('website'),
                contact_email=validated_data.get('contact_email'),
                priority=validated_data.get('priority')
            )
            return Response({"detail": "Sponsor created", "id": sponsor.sponsor_id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
