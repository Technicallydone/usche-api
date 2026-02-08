from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError

from user.enums.permission_enums import AppPermissionEnum
from user.models import AppPermission, Role
from user.serializers import (
    PermissionsResponseSerializer,
    RolesResponseSerializer,
    CreatePermissionRequestSerializer,
    RolePermissionSyncSerializer,
)
from user.permissions import HasAppPermission

class AppPermissionViewSet(viewsets.ViewSet):
    """Handles user roles and permissions
    """
    
    permission_classes = [IsAuthenticated, HasAppPermission]
    
    permission_mapping = {
        'list': AppPermissionEnum.VIEW_ROLES.value,
        'create': AppPermissionEnum.CREATE_ROLES.value,
        'remove_permissions_from_role': AppPermissionEnum.UPDATE_ROLES.value,
        'add_permissions_to_role': AppPermissionEnum.UPDATE_ROLES.value,
        'permissions': AppPermissionEnum.VIEW_PERMISSIONS.value,
        'create_permissions': AppPermissionEnum.CREATE_PERMISSIONS.value,
    }
    
    def list(self, request):
        try:
            permissions = AppPermission.permissions()
            serializer = PermissionsResponseSerializer(permissions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def create(self, request: Request):
        serializer = CreatePermissionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        try:
            permission = AppPermission.create_app_permission(
                code_name=validated_data.get('code_name'),
                description=validated_data.get('description')
            )
            
            permission_serializer = PermissionsResponseSerializer(permission)
            return Response(data=permission_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(data=e.error_dict, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['POST'], url_path='permissions/create')
    def create_permissions(self, request: Request):
        serializer = CreatePermissionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        try:
            permission = AppPermission.create_app_permission(
                code_name=validated_data.get('code_name'),
                description=validated_data.get('description')
            )
            
            permission_serializer = PermissionsResponseSerializer(permission)
            return Response(data=permission_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(data=e.error_dict, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data={"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        
    @action(detail=False, methods=["GET"], url_path="permissions")
    def permissions(self, request: Request):
        try:
            permissions = AppPermission.permissions()

            serializer = PermissionsResponseSerializer(permissions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(data=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)