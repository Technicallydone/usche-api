# user/model/app_permission_model.py
from django.db import transaction
from user.model.app_permission_model import AppPermission
from enum import Enum

class AppPermissionEnum(Enum):
    CREATE_ROLES = "create_roles"
    VIEW_ROLES = "view_roles"
    UPDATE_ROLES = "update_roles"
    DELETE_ROLES = "delete_roles"
    
    CREATE_PERMISSIONS = "create_permissions"
    VIEW_PERMISSIONS = "view_permissions"
    UPDATE_PERMISSIONS = "update_permissions"
    DELETE_PERMISSIONS = "delete_permissions"
    
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    DELETE_USERS = "delete_users"
    UPDATE_USERS = "update_users"
    VIEW_PROFILE = "view_profile"
    CHANGE_PASSWORD = "change_password"
    VIEW_USERS_REPORT = "view_users_report"
    CHANGE_USER_ROLE = "change_user_role"

    @staticmethod
    def seed_permissions():
        """Create missing permissions automatically."""
        with transaction.atomic():
            for perm in AppPermissionEnum:
                if not AppPermission.permission_exists(perm.value):
                    AppPermission.objects.create(code_name=perm.value)