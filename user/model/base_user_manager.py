from django.contrib.auth.models import BaseUserManager
from django.db import transaction

from user.enums.role import ROLE


class UserManager(BaseUserManager):
    def create_user(self, first_name: str, last_name: str, middle_name: str = None, title: str = None, email: str = None, phone_number: str = None, password: str = None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required.")
        if not phone_number:
            raise ValueError("The Phone Number field is required.")
        if not password:
            raise ValueError("The password is required")

        email = self.normalize_email(email)

        user = self.model(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            phone_number=phone_number,
            email=email,
            title=title,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    @transaction.atomic
    def create_superuser(self, first_name: str, last_name: str, middle_name: str = None, email: str = None, title: str = None, phone_number: str = None, password: str = None, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        return self.create_user(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            title=title,
            phone_number=phone_number,
            password=password,
            role=ROLE.ADMIN.value,
            **extra_fields
        )

