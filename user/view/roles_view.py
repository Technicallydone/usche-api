from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError

from user.enums.permission_enums import AppPermissionEnum
from user.model.role_model import Role
from user.serializers import (
    CreateRoleRequestSerializer,
    RolesResponseSerializer,
    RolePermissionSyncSerializer
)
from user.permissions import HasAppPermission


class AppRoleViewSet(viewsets.ViewSet):
    """Handles user roles and permissions"""

    permission_classes = [IsAuthenticated, HasAppPermission]

    # Keep your permission mapping
    permission_mapping = {
        'list': AppPermissionEnum.READ_ROLES.value,
        'create': AppPermissionEnum.CREATE_ROLES.value,
        'change_role_permissions': AppPermissionEnum.UPDATE_ROLES.value,
    }

    def list(self, request):
        try:
            roles = Role.roles()
            serializer = RolesResponseSerializer(roles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request: Request):
        serializer = CreateRoleRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            role = Role.create(name=validated_data.get('name'))
            role_serializer = RolesResponseSerializer(role)
            return Response(role_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(e.error_dict, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=["put"], url_path="change-permissions")
    def change_role_permissions(self, request: Request, pk=None):
        """
        Sync role permissions. Permissions not in the list will be removed,
        new ones will be added, and existing ones kept.
        """
        
        if pk is None:
            return Response({"detail": "Role ID is required in the URL."}, status=status.HTTP_406_NOT_ACCEPTABLE)
        
        serializer = RolePermissionSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        permission_ids = validated_data.get("permission_ids")

        try:
            role = Role.sync_permissions(role_id=pk, permission_ids=permission_ids)
            return Response(data=RolesResponseSerializer(role).data, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({"detail": e.detail}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"detail": e.error_dict}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
