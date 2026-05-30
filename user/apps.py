from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user"
    
    def ready(self):
        from user.enums.permission_enums import AppPermissionEnum
        from user.seeders.role_seeder import RoleSeeder

        # Seed permissions first
        AppPermissionEnum.seed_permissions()

        RoleSeeder.seed_default_roles()
