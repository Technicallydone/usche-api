from typing import Optional
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import EmailValidator
from django.db import models
from conference.models import Conference
from theme.models import MainTheme, SubTheme
from user.enums.invitation_status import InvitationStatusEnum
from user.enums.title import TITLE_ENUM
from user.enums.user_role_action_enum import UserRoleActionEnum
from user.model.role_model import Role
from utils.validator import validate_phone_number
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound

class UserManager(BaseUserManager["User"]):
    def create_user(
        self, 
        first_name: str, 
        last_name: str, 
        middle_name: str = None, 
        title: str = None, 
        email: str = None, 
        phone_number: str = None, 
        password: str = None, 
        **extra_fields
    ):
        if not email:
            raise ValidationError(message="The Email field is required.")
        if not phone_number:
            raise ValidationError("The Phone Number field is required.")
        if not password:
            raise ValidationError("The password is required")

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
    def create_superuser(
        self, 
        first_name: str, 
        last_name: str, 
        middle_name: str = None, 
        email: str = None, 
        title: str = None, 
        phone_number: str = None, 
        password: str = None, 
        **extra_fields
    ):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValidationError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValidationError("Superuser must have is_staff=True.")

        return self.create_user(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            title=title,
            phone_number=phone_number,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    phone_number = models.CharField(max_length=15, validators=[validate_phone_number])
    email = models.EmailField(max_length=100, unique=True, null=False, blank=False, validators=[EmailValidator(message="Please enter a valid email address")])
    country = models.CharField(max_length=20, null=False, blank=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    
    resend_activation_email = models.BooleanField(default=False)
    has_sent_activation_email = models.BooleanField(default=False)
    
    objects = UserManager()

    title = models.CharField(max_length=255, null=False, blank=False, choices=TITLE_ENUM.choices())  
    affiliation = models.TextField()
    occupation = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'title']
    
    class Meta:
        db_table = 'users'
        app_label = 'user'

    def __str__(self) -> str:
        """Show full name

        Returns:
            str: full name value
        """
        return str(self.full_name)
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.middle_name} {self.last_name}"
    
    @property
    def invitation_status(self) -> bool:
        return self.has_sent_activation_email
    
    @property
    def invitation_sent(self):
        return self.has_sent_activation_email
    
    @classmethod
    def users_without_abstract_and_payment(cls, conference: Conference):
        from abstracts.models import Abstract
        from payment.models import Payment

        theme = MainTheme.get_theme_by_conference(conference)
        
        if theme is None:
            return cls.objects.none()
        
        sub_themes = SubTheme.objects.filter(theme=theme)

        # Get users who have abstracts in this conference (via subthemes)
        users_with_abstracts = Abstract.objects.filter(sub_theme__in=sub_themes).values_list('user_id', flat=True).distinct()

        # Get users who have payments for this conference
        users_with_payments = Payment.objects.filter(conference=conference).values_list('user_id', flat=True).distinct()

        # Exclude users who have either abstracts or payments for this conference
        return cls.objects.exclude(
            Q(user_id__in=users_with_payments)
        ).filter(is_active=True, is_superuser=False)
    
    @classmethod
    def total_users(cls):
        return cls.objects.count()
    
    @classmethod
    def get_user_by_id(cls, user_id: uuid.UUID) -> 'User':
        return cls.objects.filter(user_id=user_id).first()
    
    @classmethod
    def get_user_by_email(cls, email: str):
        return cls.objects.filter(email=email).first()
    
    @classmethod
    def get_users_by_ids(cls, user_ids):
        return cls.objects.filter(user_id__in=user_ids)
    
    @classmethod
    def create_user(
        cls,
        title: str,
        affiliation: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        email: str,
        country: str,
        password: str,
        occupation: str,
        middle_name: Optional[str] = None,
    ) -> "User":
        """
        Class method to create a User instance.

        Args:
            title (str): User's title.
            affiliation (str): User's affiliation.
            first_name (str): First name.
            middle_name (Optional[str]): Middle name (optional).
            last_name (str): Last name.
            phone_number (str): Unique phone number.
            email (str): Unique email address.
            country (str): Country of the user.
            password (str): User's raw password.

        Returns:
            User: The created User instance.
        """
        user = cls(
            title=title,
            affiliation=affiliation,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            phone_number=phone_number,
            email=email,
            country=country,
            password=password,
            occupation=occupation,
        )
        user.set_password(raw_password=password)
        user.save()
        return user
    
    @classmethod
    def search_users(cls, search_query: str = None, staff: bool = None):
        """
        Return users filtered by full name and/or staff status.

        Args:
            name (str, optional): Partial or full name to search (case-insensitive). Defaults to None.
            staff (bool, optional): 
                True = staff only
                False = non-staff only
                None = ignore staff filter
        Returns:
            QuerySet: filtered User queryset
        """
        filters = Q(is_superuser=False)
        
        if staff is True:
            filters &= Q(is_staff=True)
        elif staff is False:
            filters &= Q(is_staff=False)
        
        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        return cls.objects.filter(filters).order_by('-created_at')
    
    @classmethod
    def change_role(cls, user_id: uuid.UUID, role_id: uuid.UUID, action: UserRoleActionEnum):
        """
        Assign or unassign a role to a user.
        """
        user = cls.objects.filter(user_id=user_id).first()
        if user is None:
            raise NotFound(detail="User with the given ID does not exist.")

        role = Role.objects.filter(id=role_id).first()
        if not role:
            raise NotFound(detail="Role with the given ID does not exist.")

        if action == UserRoleActionEnum.ASSIGN:
            user.role = role
        elif action == UserRoleActionEnum.UNASSIGN:
            user.role = None
        else:
            raise ValidationError("Invalid action. Must be 'assign' or 'unassign'.")

        user.save()
        return user
    
    @classmethod
    def users(
        cls,
        conference: Conference,
        filter_type: str = InvitationStatusEnum.ALL.value,
        search_query: Optional[str] = None,
        is_active: bool = True
    ):
        """
        Filters users based on the type of filter (ALL, INVITED, NOT_INVITED, INVITED_NOT_SENT)
        """
        from invitation.models import Invitation
        
        filter_type = InvitationStatusEnum.validate(filter_type)

        filters = Q(is_superuser=False, is_active=is_active)
        
        invitation_filters = Q(conference=conference)
        
        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        if filter_type == InvitationStatusEnum.ALL.value:
            users = cls.objects.filter(filters).order_by('-created_at')
            invitations = Invitation.objects.filter(invitation_filters)
            users_with_status = []
            for user in users:
                invitation = invitations.filter(user=user).first()
                users_with_status.append({
                    'user': user,
                    'invitation_status': bool(invitation),
                    'invitation_sent': invitation.invitation_sent if invitation else False
                })
            return users_with_status
        
        elif filter_type == InvitationStatusEnum.INVITED.value:
            invited_users = User.objects.filter(filters, invitations__isnull=False).distinct().order_by('-created_at')
            return [{'user': user, 'invitation_status': True, 'invitation_sent': user.invitations.first().invitation_sent} for user in invited_users]

        elif filter_type == InvitationStatusEnum.NOT_INVITED.value:
            not_invited_users = User.objects.filter(filters, invitations__isnull=True).order_by('-created_at')
            return [{'user': user, 'invitation_status': False, 'invitation_sent': False} for user in not_invited_users]

        elif filter_type == InvitationStatusEnum.INVITED_NOT_SENT.value:
            invited_not_sent_users = User.objects.filter(filters, invitations__invitation_sent=False).order_by('-created_at')
            return [{'user': user, 'invitation_status': True, 'invitation_sent': False} for user in invited_not_sent_users]

        else:
            raise ValidationError("Invalid filter_type. Must be one of: 'ALL', 'INVITED', 'NOT_INVITED', 'INVITED_NOT_SENT'.")

    @classmethod
    def user_report(cls, search_query: str = None):
        filters = Q()
        
        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        return cls.objects.filter(filters).order_by('-created_at')