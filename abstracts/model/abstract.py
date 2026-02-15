from typing import Tuple
import uuid
from django.db import models, transaction
from django.db.models import Q
from abstracts.enums.abstract_status import AbstractStatus
from payment.enums.payment_status import PaymentStatus
from theme.model.main_theme import MainTheme
from theme.models import SubTheme
from user.models import User
from utils.upload_document_to import upload_abstract_document
from utils.validator import validate_document_type
from django.utils import timezone

class Abstract(models.Model):
    abstract_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sub_theme = models.ForeignKey(SubTheme, on_delete=models.CASCADE, related_name="abstracts")
    title = models.CharField(max_length=255, null=False, blank=False)
    authors = models.TextField(null=True, blank=True, help_text="Comma-separated list of author names")
    content = models.TextField(null=False, blank=False)
    keywords = models.CharField(max_length=255, null=False, blank=False, help_text="3-5 keywords separated by commas.")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="abstracts")
    document = models.FileField(
        upload_to=upload_abstract_document,
        validators=[validate_document_type],
    )
    status = models.CharField(
        max_length=20,
        choices=AbstractStatus.choices(),
        default=AbstractStatus.default(),
    )
    sent_at = models.DateTimeField(null=True, blank=True, help_text="When the payment request email was sent.")
    comment = models.TextField(blank=True, null=True, help_text="Optional comment regarding the abstract status.")
    is_payment_done = models.BooleanField(default=False, help_text="Indicates whether payment has been completed.")
    created_at = models.DateTimeField(default=timezone.now, editable=False)


    class Meta:
        db_table = 'abstracts'
        app_label = 'abstracts'

    def __str__(self):
        return self.title
    
    def is_owned_by(self, user: User):
        """Returns True if the given user owns this abstract, otherwise False."""
        return self.user == user
    
    def mark_payment_done(self):
        self.is_payment_done = True
        self.status = AbstractStatus.APPROVED.value
        self.save(update_fields=["is_payment_done", "status"])
        
    @classmethod
    def users_without_abstract(cls):
        return cls.objects.exclude(
            pk__in=Abstract.objects.values_list('user_id', flat=True)
        )
    
    @classmethod
    def create_abstract(cls, title: str, content: str, keywords: str, sub_theme: SubTheme, user: User, document, authors: str) -> 'Abstract':
        """
        Class method to create an Abstract instance from the provided arguments.

        Args:
            title (str): The title of the abstract.
            content (str): The content of the abstract.
            keywords (str): Keywords related to the abstract.
            sub_theme (SubTheme): The sub-theme object related to the abstract.
            user (User): The user object submitting the abstract.
            document (File): The document file related to the abstract.

        Returns:
            Abstract: The created Abstract instance.
        """
        abstract = cls(
            title=title,
            content=content,
            keywords=keywords,
            sub_theme=sub_theme,
            user=user,
            document=document,
            authors=authors
        )

        abstract.save()

        return abstract

    @classmethod
    def get_abstracts_by_status(cls, main_theme: MainTheme, status: str = None, search_query: str = None):
        sub_themes = SubTheme.objects.filter(theme=main_theme)
        filters = Q(sub_theme__in=sub_themes)

        if status and status != "All":
            filters &= Q(status=status)

        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(user__first_name__icontains=search_query) |
                Q(user__middle_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        return cls.objects.filter(filters)
        
    @classmethod
    def abstract_stats(cls, main_theme: MainTheme) -> Tuple[int, int, int, int]:
        sub_themes = SubTheme.objects.filter(theme=main_theme)
        sub_theme_abstracts = cls.objects.filter(sub_theme__in=sub_themes)

        total_abstracts = sub_theme_abstracts.count()
        total_paid_abstracts = sub_theme_abstracts.filter(is_payment_done=True).count()
        total_unpaid_abstracts = total_abstracts - total_paid_abstracts
        total_approved_abstracts = sub_theme_abstracts.filter(status=AbstractStatus.APPROVED.value).count()

        return total_abstracts, total_paid_abstracts, total_unpaid_abstracts, total_approved_abstracts
    
    @classmethod
    def conference_abstract_report(cls, main_theme: MainTheme, abstract_status: str = None):
        sub_themes = SubTheme.objects.filter(theme=main_theme)
        sub_theme_ids = list(sub_themes.values_list('sub_theme_id', flat=True))

        filters = Q(sub_theme__in=sub_theme_ids)

        if abstract_status:
            filters &= Q(status=abstract_status)


        return cls.objects.filter(filters).order_by('-created_at')

    @classmethod
    def mark_as_rejected(cls, abstract_id: uuid.UUID, comment: str = None):
        """Reject an abstract with an optional comment."""
        abstract = cls.objects.filter(abstract_id=abstract_id).first()
        if abstract and abstract.status in {AbstractStatus.PENDING.value}:
            abstract.status = AbstractStatus.REJECTED.value
            abstract.comment = comment
            abstract.save(update_fields=["status", "comment"])
            return abstract
        return None

    @classmethod
    @transaction.atomic
    def mark_as_approved(cls, abstract_id: uuid.UUID, comment: str):
        """Approve an abstract if payment is done."""
        abstract = cls.objects.filter(abstract_id=abstract_id).select_for_update().first()
        
        abstract.status = AbstractStatus.APPROVED.value
        abstract.comment = comment
        abstract.save(update_fields=["status", "comment"])
        return abstract
    
    @classmethod
    def get_abstract_by_id(cls, abstract_id: uuid.UUID):
        return cls.objects.filter(abstract_id=abstract_id).first()
    
    @classmethod
    def retrieve_abstract(cls, abstract_id: uuid.UUID = None, user: User = None):
        filters = Q()

        if user:
            filters &= Q(user=user)

        if abstract_id:
            filters &= Q(abstract_id=abstract_id)

        return cls.objects.filter(filters).first()
    
    @classmethod
    def get_conference_abstracts(cls, main_theme: MainTheme, search_query: str = None):
        sub_themes = SubTheme.objects.filter(theme=main_theme)

        filters = Q(sub_theme__in=sub_themes)

        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(user__first_name__icontains=search_query) |
                Q(user__middle_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        return cls.objects.filter(filters)
