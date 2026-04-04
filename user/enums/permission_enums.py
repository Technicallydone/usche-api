# user/model/app_permission_model.py
from enum import Enum

class AppPermissionEnum(str, Enum):
    # Roles
    CREATE_ROLES = "permission.create.roles"
    READ_ROLES = "permission.view.roles"
    UPDATE_ROLES = "permission.update.roles"
    DELETE_ROLES = "permission.delete.roles"
    ADD_PERMISSIONS = "permission.add.permissions"
    REMOVE_PERMISSIONS = "permission.remove.permissions"
    ASSIGN_USER_ROLE = "permission.assign.user.role"
    REMOVE_USER_ROLE = "permission.remove.user.role"
    CHANGE_USER_ROLE = "permission.change.user.role"

    # Permissions
    CREATE_PERMISSIONS = "permission.create.permissions"
    READ_PERMISSIONS = "permission.view.permissions"
    UPDATE_PERMISSIONS = "permission.update.permissions"
    DELETE_PERMISSIONS = "permission.delete.permissions"

    # Users
    READ_USERS = "permission.view.users"
    CREATE_USERS = "permission.create.users"
    UPDATE_USERS = "permission.update.users"
    DELETE_USERS = "permission.delete.users"
    READ_USERS_REPORT = "permission.view.users.report"
    UPDATE_STAFF_STATUS = "permission.update.staff.status"
    MANAGE_STAFF_MEMBERSHIP = "permission.manage.staff.membership"

    # Profile & Password
    READ_PROFILE = "permission.view.profile"
    CHANGE_PASSWORD = "permission.change.password"
    
    # Statistics
    READ_CONFERENCE_STATS = "permission.view.conference.stats"
    
    SIGN_OUT = "permission.sign.out"
    
    # Conference Management
    MANAGE_CONFERENCE = "permission.manage.conference"
    READ_CONFERENCE = "permission.view.conference"
    UPDATE_CONFERENCE = "permission.update.conference"
    DELETE_CONFERENCE = "permission.delete.conference"

    @staticmethod
    def seed_permissions():
        """Create missing permissions automatically in DB."""
        from django.db import transaction
        from user.model.app_permission_model import AppPermission

        with transaction.atomic():
            for perm in AppPermissionEnum:
                if not AppPermission.permission_exists(perm):
                    AppPermission.objects.create(code_name=perm)