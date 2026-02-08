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
    VIEW_USERS_REPORT = "view_users_report"
    CHANGE_USER_ROLE = "change_user_role"