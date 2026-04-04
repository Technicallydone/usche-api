from django.apps import AppConfig



class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user"
    
    def ready(self):
        from user.model.role_model import Role
        from user.enums.permission_enums import AppPermissionEnum

        # Seed permissions first
        AppPermissionEnum.seed_permissions()

        # Seed default role with default permissions
        # Role.seed_default_role()
        # Role.seed_admin_role()
        Role.seed_default_roles()
