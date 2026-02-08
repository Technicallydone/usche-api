from typing import Optional
from django.db import models
from django.core.exceptions import ValidationError
from uuid import uuid4

class AppPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    code_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.code_name

    class Meta:
        db_table = "permissions"
        app_label = "user"
        
    @staticmethod
    def permissions():
        return AppPermission.objects.all()
    
    @staticmethod
    def permission_exists(code_name: str) -> bool:
        return AppPermission.objects.filter(code_name=code_name.strip()).exists()
    
    @staticmethod
    def create_app_permission(
        code_name: str,
        description: Optional['str']
    ):
        try:
            if AppPermission.permission_exists(code_name=code_name):
                raise ValidationError({"code_name": f"Permission with code name '{code_name} already exists'"})
            
            permission = AppPermission.objects.create(
                code_name=code_name,
                description=description
            )
            
            return permission
        except ValidationError as e:
            raise e
        except Exception as e:
            raise e