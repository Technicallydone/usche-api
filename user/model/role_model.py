from typing import List
from django.db import models
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound
from uuid import uuid4, UUID

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


