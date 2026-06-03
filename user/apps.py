from django.apps import AppConfig
from django.db import utils


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user"
    
    def ready(self):
        from user.enums.permission_enums import AppPermissionEnum
        from user.seeders.role_seeder import RoleSeeder

        
        try:
            AppPermissionEnum.seed_permissions()
            RoleSeeder.seed_default_roles()
        except (utils.ProgrammingError, utils.OperationalError):
            # The table doesn't exist yet (e.g., during makemigrations/migrate)
            pass
