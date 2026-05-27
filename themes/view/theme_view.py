import os
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
import logging

from abstracts.models import Abstract
from themes.serializers import (
    CreateMainThemeSerializer,
    CreateSubThemeSerializer,
    UpdateMainThemeSerializer,
    BulkUpdateSubThemesSerializer
)
from themes.models import SubTheme, MainTheme
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission

logger = logging.getLogger(__name__)

class ThemeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    
    permission_mapping = {
        'create': AppPermissionEnum.CREATE_MAIN_THEME.value,
        'create_sub_theme': AppPermissionEnum.CREATE_SUB_THEME.value,
        'update': AppPermissionEnum.UPDATE_MAIN_THEME.value,
        'update_sub_theme': AppPermissionEnum.UPDATE_SUB_THEME.value,
        'delete_sub_theme': AppPermissionEnum.DELETE_SUB_THEME.value,
    }
    
    @action(detail=False, methods=["delete"], url_path="sub/delete/(?P<sub_theme_id>[^/.]+)")
    def delete_sub_theme(self, request: Request, sub_theme_id=None):
        try:
            sub_theme = SubTheme.objects.get(sub_theme_id=sub_theme_id)

            has_abstracts = Abstract.objects.filter(
                sub_theme=sub_theme
            ).exists()

            if has_abstracts:
                return Response(
                    {
                        "detail": (
                            "This sub-theme cannot be deleted because "
                            "it is already associated with abstracts."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sub_theme.delete()

            return Response(
                data={
                    "detail": "Sub-theme deleted successfully",
                    "id": sub_theme_id,
                },
                status=status.HTTP_200_OK,
            )

        except SubTheme.DoesNotExist:
            return Response(
                {"detail": "Sub-theme not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.exception("Failed to delete sub-theme")

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=["put"], url_path="sub/update")
    def update_sub_theme(self, request: Request):
        serializer = BulkUpdateSubThemesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        theme_id = validated_data.get("theme_id")
        sub_themes = validated_data.get("sub_themes")

        try:
            updated_items = []

            for item in sub_themes:
                sub_theme = SubTheme.objects.get(
                    sub_theme_id=item["id"],
                    theme_id=theme_id,
                )

                sub_theme.title = item["title"]
                sub_theme.description = item["description"]
                sub_theme.save(update_fields=["title", "description"])

                updated_items.append(sub_theme.sub_theme_id)

            return Response(
                {
                    "detail": "Sub-themes updated successfully",
                    "updated_ids": updated_items,
                },
                status=status.HTTP_200_OK,
            )

        except SubTheme.DoesNotExist:
            return Response(
                {"detail": "One or more sub-themes not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request: Request, pk=None):
        serializer = UpdateMainThemeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        try:
            theme = MainTheme.objects.get(pk=pk)

            theme.title = validated_data.get("title")

            theme.description = validated_data.get("description")

            theme.save(update_fields=["title", "description"])

            return Response(
                data={
                    "detail": "Main theme updated successfully",
                    "id": theme.theme_id,
                },
                status=status.HTTP_200_OK,
            )

        except MainTheme.DoesNotExist:
            return Response(
                {"detail": "Main theme not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create(self, request: Request):
        serializer = CreateMainThemeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            main_theme = MainTheme.objects.create(
                conference_id=validated_data.get('conference_id'),
                title=validated_data.get('title'),
                description=validated_data.get('description'),
            )
            return Response(
                data={"detail": "Main theme created successfully", "id": main_theme.theme_id},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='sub/create')
    def create_sub_theme(self, request: Request):
        serializer = CreateSubThemeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            sub_theme = SubTheme.objects.create(
                theme_id=validated_data.get('theme_id'),
                title=validated_data.get('title'),
                description=validated_data.get('description'),
            )
            return Response(
                data={"detail": "Subtheme created successfully", "id": sub_theme.sub_theme_id},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
