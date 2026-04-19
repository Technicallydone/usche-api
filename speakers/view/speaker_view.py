import os
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
import logging

from conference.model.conference import Conference
from speakers.models import Speaker
from speakers.serializers import CreateSpeakerSerializer
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission

logger = logging.getLogger(__name__)

class SpeakerViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        'create': AppPermissionEnum.CREATE_SPEAKER.value
    }

    def create(self, request: Request):
        serializer = CreateSpeakerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            conference = Conference.get_conference_by_id(conference_id=validated_data.get('conference_id'))
            
            if conference is None:
                return Response(data={"detail": "Conference not found"}, status=status.HTTP_404_NOT_FOUND)
            
            speaker = Speaker.objects.create(
                conference=conference,
                speaker_category=validated_data.get('speaker_category'),
                name=validated_data.get('name'),
                title=validated_data.get('title'),
                specialization=validated_data.get('specialization'),
                organization=validated_data.get('organization'),
                role=validated_data.get('role'),
                biography=validated_data.get('biography'),
                speaker_image=validated_data.get('speaker_image'),
            )
            return Response({"detail": "Speaker created", "id": speaker.speaker_id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
