import os
from typing import Any, Dict, List
from django.http import FileResponse, Http404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
import logging

from conference.model.conference import Conference
from sponsors.models import Sponsor
from sponsors.serializers import CreateSponsorSerializer, UpdateSponsorSerializer
from usche_app import settings
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission
from django.db import transaction

logger = logging.getLogger(__name__)

class SponsorViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny, HasAppPermission]
    
    permission_mapping = {
        'create': AppPermissionEnum.CREATE_SPONSOR.value,
        'bulk_update_sponsors': AppPermissionEnum.UPDATE_SPONSOR.value,
    }
    
    @action(detail=False, methods=['get'], url_path='sponsor-logo/(?P<image_id>[^/]+)')
    def sponsor_logo(self, request, image_id):
        try:
            sponsor_data = Sponsor.objects.get(sponsor_id=image_id)
            
            image_filename = sponsor_data.logo.name
            image_path = os.path.join(settings.MEDIA_ROOT, image_filename)

            if not os.path.exists(image_path):
                raise Http404("Image not found")

            return FileResponse(open(image_path, 'rb'), content_type="image/jpeg")

        except Sponsor.DoesNotExist:
            logger.error(f"Sponsor with id {image_id} not found.")
            return Response(
                data={"detail": "Sponsor not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"Error while retrieving sponsor logo: {e}")
            return Response(
                data={"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["delete"], url_path="delete")
    def delete_sponsor(self, request: Request, pk=None):
        try:
            with transaction.atomic():
                sponsor = Sponsor.objects.select_for_update().filter(
                    sponsor_id=pk
                ).first()

                if not sponsor:
                    return Response(
                        {"detail": "Sponsor not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if sponsor.logo:
                    sponsor.logo.delete(save=False)

                sponsor.delete()

            return Response(
                {"detail": "Sponsor deleted successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Sponsor delete failed")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @staticmethod
    def extract_sponsors_from_request(
        data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        sponsors: List[Dict[str, Any]] = []

        index = 0

        while data.get(f"sponsors[{index}][sponsor_id]") is not None:
            sponsors.append({
                "sponsor_id": data.get(
                    f"sponsors[{index}][sponsor_id]"
                ),
                "name": data.get(
                    f"sponsors[{index}][name]"
                ),
                "priority": data.get(
                    f"sponsors[{index}][priority]"
                ),
                "website": data.get(
                    f"sponsors[{index}][website]"
                ),
                "contact_email": data.get(
                    f"sponsors[{index}][contact_email]"
                ),
                "logo": data.get(
                    f"sponsors[{index}][logo]"
                ),
            })

            index += 1

        return sponsors

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update_sponsors(self, request: Request):
        try:
            raw_sponsors = self.extract_sponsors_from_request(
                request.data
            )

            serializer = UpdateSponsorSerializer(
                data=raw_sponsors,
                many=True
            )

            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data

            with transaction.atomic():
                updated_ids = []

                for item in validated_data:
                    sponsor = Sponsor.objects.select_for_update().filter(
                        sponsor_id=item.get("sponsor_id")
                    ).first()

                    if not sponsor:
                        continue

                    sponsor.name = item.get(
                        "name",
                        sponsor.name
                    )

                    sponsor.website = item.get(
                        "website",
                        sponsor.website
                    )

                    sponsor.contact_email = item.get(
                        "contact_email",
                        sponsor.contact_email
                    )

                    sponsor.priority = item.get(
                        "priority",
                        sponsor.priority
                    )

                    new_logo = item.get("logo")

                    if new_logo:
                        # delete old logo if it exists
                        if sponsor.logo:
                            sponsor.logo.delete(save=False)

                        sponsor.logo = new_logo

                    sponsor.save()

                    updated_ids.append(str(sponsor.sponsor_id))

            return Response(
                {
                    "detail": "Sponsors updated successfully",
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
            logger.exception("Bulk sponsor update failed")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
