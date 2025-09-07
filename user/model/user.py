from typing import Optional
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import EmailValidator
from django.db import models
from conference.models import Conference
from theme.models import MainTheme, SubTheme
from user.enums.role import ROLE
from user.enums.title import TITLE_ENUM
from .base_user_manager import UserManager
from utils.validator import validate_phone_number
from django.utils import timezone
from django.db.models import Q


class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, validators=[validate_phone_number])
    email = models.EmailField(max_length=100, unique=True, null=False, blank=False, validators=[EmailValidator(message="Please enter a valid email address")])
    country = models.CharField(max_length=20, null=False, blank=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE.choices())
    
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
        db_table = 'user'
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
        ).filter(is_active=True, is_superuser=False, role=ROLE.ATTENDEE.value)
    
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
            role=ROLE.ATTENDEE.value
        )
        user.set_password(raw_password=password)
        user.save()
        return user
    
    @classmethod
    def user_list(cls, search_query: str = None, ):
        filters = Q(is_superuser=False, is_active=True)
        filters &= ~Q(role=ROLE.ADMIN.value)

        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        return cls.objects.filter(filters).order_by('-created_at')
    
    @classmethod
    def users(cls, search_query: str = None, ):
        filters = Q(is_superuser=False)
        filters &= ~Q(role=ROLE.ADMIN.value)

        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        return cls.objects.filter(filters).order_by('-created_at')
