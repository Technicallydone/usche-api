from typing import List
from django.db import models, transaction
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound
from uuid import uuid4, UUID

from user.enums.default_roles_enum import DefaultAppRolesEnum
from user.enums.permission_enums import AppPermissionEnum
from user.model.app_permission_model import AppPermission

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField(AppPermission, blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        db_table = "roles"
        app_label = "user"
        
    def seed_default_roles():
        """
        Seed all default roles and assign appropriate permissions.
        Admin: all permissions
        User: minimal permissions (view profile, change password)
        Organizer: view users, view users report
        Bursar: view users, update users, view users report
        """
        with transaction.atomic():
            for role_enum in DefaultAppRolesEnum:
                role_name = role_enum.value
                role, created = Role.objects.get_or_create(name=role_name)

                if created:
                    if role_enum == DefaultAppRolesEnum.Admin:
                        # Admin gets all permissions
                        all_permissions = AppPermission.objects.filter(
                            code_name__in=[perm for perm in AppPermissionEnum]
                        )
                        role.permissions.set(all_permissions)

                    elif role_enum == DefaultAppRolesEnum.User:
                        # Default user gets minimal permissions
                        default_permissions = AppPermission.objects.filter(
                            code_name__in=[
                                AppPermissionEnum.READ_PROFILE,
                                AppPermissionEnum.CHANGE_PASSWORD,
                                AppPermissionEnum.SIGN_OUT,
                                AppPermissionEnum.READ_PROFILE,
                                AppPermissionEnum.READ_OWN_CONFERENCE_JOIN_REQUEST,
                                AppPermissionEnum.REQUEST_JOIN_CONFERENCE,
                                AppPermissionEnum.READ_OWN_PAYMENTS,
                                AppPermissionEnum.DOWNLOAD_PAYMENT_SLIP,
                                AppPermissionEnum.DOWNLOAD_OWN_ABSTRACT_DOCUMENT,
                                AppPermissionEnum.DOWNLOAD_ABSTRACT_DOCUMENT
                            ]
                        )
                        role.permissions.set(default_permissions)

                    elif role_enum == DefaultAppRolesEnum.Organizer:
                        # Organizer permissions (example: view users and report)
                        organizer_permissions = AppPermission.objects.filter(
                            code_name__in=[
                                AppPermissionEnum.READ_USERS,
                                AppPermissionEnum.READ_USERS_REPORT,
                                AppPermissionEnum.SIGN_OUT,
                                AppPermissionEnum.READ_PROFILE,
                                AppPermissionEnum.READ_OWN_CONFERENCE_JOIN_REQUEST,
                                AppPermissionEnum.REQUEST_JOIN_CONFERENCE,
                                AppPermissionEnum.READ_OWN_PAYMENTS,
                                AppPermissionEnum.DOWNLOAD_PAYMENT_SLIP,
                                AppPermissionEnum.DOWNLOAD_OWN_ABSTRACT_DOCUMENT,
                                AppPermissionEnum.DOWNLOAD_ABSTRACT_DOCUMENT
                            ]
                        )
                        role.permissions.set(organizer_permissions)

                    elif role_enum == DefaultAppRolesEnum.Bursar:
                        # Bursar permissions (example: view/update users and report)
                        bursar_permissions = AppPermission.objects.filter(
                            code_name__in=[
                                AppPermissionEnum.READ_USERS,
                                AppPermissionEnum.UPDATE_USERS,
                                AppPermissionEnum.READ_USERS_REPORT,
                                AppPermissionEnum.SIGN_OUT,
                                AppPermissionEnum.READ_PROFILE,
                                AppPermissionEnum.READ_OWN_CONFERENCE_JOIN_REQUEST,
                                AppPermissionEnum.REQUEST_JOIN_CONFERENCE,
                                AppPermissionEnum.READ_OWN_PAYMENTS,
                                AppPermissionEnum.DOWNLOAD_PAYMENT_SLIP,
                                AppPermissionEnum.DOWNLOAD_OWN_ABSTRACT_DOCUMENT,
                                AppPermissionEnum.DOWNLOAD_ABSTRACT_DOCUMENT
                            ]
                        )
                        role.permissions.set(bursar_permissions)

                    role.save()

        print("All default roles seeded successfully!")
    
    @staticmethod
    def seed_default_role(default_role_name=DefaultAppRolesEnum.default()):
        """
        Ensure the default role exists with default permissions.
        """

        with transaction.atomic():
            role, created = Role.objects.get_or_create(name=default_role_name)

            if created:
                default_permissions = AppPermission.objects.filter(
                    code_name__in=[
                        AppPermissionEnum.READ_PROFILE.value,
                        AppPermissionEnum.CHANGE_PASSWORD.value
                    ]
                )
                role.permissions.set(default_permissions)
                role.save()

            return role
        
    def seed_admin_role(admin_role_name=DefaultAppRolesEnum.admin()):
        """
        Ensure the admin role exists and assign all permissions.
        """

        with transaction.atomic():
            admin_role, created = Role.objects.get_or_create(name=admin_role_name)

            # Get all permissions from AppPermissionEnum
            all_permissions = AppPermission.objects.filter(
                code_name__in=[perm for perm in AppPermissionEnum]
            )

            admin_role.permissions.set(all_permissions)
            admin_role.save()

            return admin_role
        
    @staticmethod
    def find_by_id(id: UUID):
        return Role.objects.filter(id=id).first()
        
    @staticmethod
    def roleExists(name:str) -> bool:
        return Role.objects.filter(name=name.strip()).exists()
    
    @staticmethod
    def sync_permissions(role_id: UUID, permission_ids: list):
        """
        Sync role permissions: remove permissions not in the list, add new ones, keep existing in the list.
        """
        role = Role.objects.filter(id=role_id).first()
        if not role:
            raise NotFound(detail="Role not found")

        # Fetch permission objects
        permissions = list(AppPermission.objects.filter(id__in=permission_ids))

        # Set role.permissions to exactly match the permission_ids
        role.permissions.set(permissions)  # Django handles adding/removing automatically
        role.save()

        return role
        
    @staticmethod
    def create(
        name: str
    ):
        try:
            if Role.roleExists(name=name):
                raise ValidationError({"name": f"Role with name '{name}' already exists"})
            role = Role.objects.create(name=name)
        
            return role
        except ValidationError as e:
            raise e
        except Exception as e:
            raise e
        
    @staticmethod
    def roles():
        return Role.objects.prefetch_related("permissions").all()


