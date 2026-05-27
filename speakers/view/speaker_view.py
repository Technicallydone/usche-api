import os
from typing import Any, Dict, List
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
import logging

from conference.model.conference import Conference
from speakers.models import Speaker
from speakers.serializers import CreateSpeakerSerializer, UpdateSpeakerSerializer, BulkUpdateSpeakerSerializer
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission
from django.db import transaction

logger = logging.getLogger(__name__)

class SpeakerViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]

    permission_mapping = {
        'create': AppPermissionEnum.CREATE_SPEAKER.value,
        'update': AppPermissionEnum.UPDATE_SPEAKER.value,
        'delete_speaker': AppPermissionEnum.DELETE_SPEAKER.value,
    }
    
    @staticmethod
    def extract_speakers_from_request(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        speakers: List[Dict[str, Any]] = []
        index = 0

        while data.get(f"speakers[{index}][speaker_id]") is not None:
            speakers.append({
                "speaker_id": data.get(f"speakers[{index}][speaker_id]"),
                "speaker_category": data.get(f"speakers[{index}][speaker_category]"),
                "name": data.get(f"speakers[{index}][name]"),
                "title": data.get(f"speakers[{index}][title]"),
                "organization": data.get(f"speakers[{index}][organization]"),
                "role": data.get(f"speakers[{index}][role]"),
                "biography": data.get(f"speakers[{index}][biography]"),
                "specialization": data.get(f"speakers[{index}][specialization]"),
                "speaker_image": data.get(f"speakers[{index}][speaker_image]"),
            })
            index += 1

        return speakers
    
    @action(
        detail=False,
        methods=["put"],
        url_path="bulk-update"
    )
    def bulk_update_speakers(self, request: Request):
        try:
            raw_speakers = self.extract_speakers_from_request(request.data)
            
            print(raw_speakers)

            serializer = BulkUpdateSpeakerSerializer(data=raw_speakers, many=True)
            serializer.is_valid(raise_exception=True)

            validated_speakers = serializer.validated_data

            with transaction.atomic():
                updated_ids = []

                for item in validated_speakers:
                    speaker = Speaker.objects.select_for_update().filter(
                        speaker_id=item.get("speaker_id")
                    ).first()

                    if not speaker:
                        continue

                    speaker.speaker_category = item.get("speaker_category")
                    speaker.name = item.get("name")
                    speaker.title = item.get("title")
                    speaker.organization = item.get("organization")
                    speaker.role = item.get("role", "")
                    speaker.biography = item.get("biography")
                    speaker.specialization = item.get("specialization", "")

                    new_image = item.get("speaker_image")

                    if new_image:
                        # delete old image if it exists
                        if speaker.speaker_image:
                            speaker.speaker_image.delete(save=False)

                        speaker.speaker_image = new_image

                    speaker.save()
                    updated_ids.append(str(speaker.speaker_id))

            return Response(
                {
                    "detail": "Speakers updated successfully",
                    "updated_ids": updated_ids,
                },
                status=status.HTTP_200_OK,
            )

        except Speaker.DoesNotExist:
            return Response(
                {"detail": "Speaker not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError as e:
            return Response(
                {"detail": e.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception("Bulk speaker update failed")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(
        detail=False,
        methods=["delete"],
        url_path="delete/(?P<speaker_id>[^/.]+)"
    )
    def delete_speaker(self, request: Request, speaker_id=None):
        try:
            speaker = Speaker.objects.get(speaker_id=speaker_id)

            if speaker.speaker_image:
                image_path = speaker.speaker_image.path

                if os.path.isfile(image_path):
                    os.remove(image_path)

            speaker.delete()

            return Response(
                {
                    "detail": "Speaker deleted successfully",
                    "id": speaker_id,
                },
                status=status.HTTP_200_OK,
            )

        except Speaker.DoesNotExist:
            return Response(
                {"detail": "Speaker not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.exception("Failed to delete speaker")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def update(self, request: Request, pk=None):
        serializer = UpdateSpeakerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        try:
            speaker = Speaker.objects.get(pk=pk)

            for field, value in validated_data.items():
                setattr(speaker, field, value)

            speaker.save()

            return Response(
                {
                    "detail": "Speaker updated successfully",
                    "id": speaker.speaker_id,
                },
                status=status.HTTP_200_OK,
            )

        except Speaker.DoesNotExist:
            return Response(
                {"detail": "Speaker not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception("Failed to update speaker")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
