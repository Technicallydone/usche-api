from decimal import Decimal
import uuid
from enum import Enum
from typing import List, Tuple

from django.db import models
from django.db.models import Q
from abstracts.enums.payment_category import PaymentCategory
from abstracts.models import Abstract
from conference.model.conference import Conference
from payment.enums.payment_status import PaymentStatus
from user.models import User
from utils.upload_document_to import upload_payment_receipt
from utils.validator import validate_document_type


class Payment(models.Model):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    abstract = models.ForeignKey(Abstract, on_delete=models.CASCADE, related_name="payment", null=True, blank=True)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="payment", null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid")
    payment_slip = models.FileField(upload_to=upload_payment_receipt, validators=[validate_document_type], help_text="Upload payment slip")
    comment = models.TextField(null=False, blank=False)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices(),
        default=PaymentStatus.default(),
    )
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="approved_payments", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'payments'
        app_label = 'payment'

    def __str__(self):
        return f"Payment {self.payment_id} - {self.user.full_name}"
    
    @classmethod
    def payment_activity_stats(cls):
        """
        Returns statistics about users based on actual payments made.

        Output:
        {
            "total_users": int,              # total users in system
            "active_users": int,             # users who made at least one payment
            "inactive_users": int,           # users with no payments
            "active_percentage": float       # % of users who made payments
        }
        """
        from user.models import User

        total_users = User.objects.filter(is_active=True, is_superuser=False).count()

        # Users who have made at least one payment
        active_users = User.objects.filter(
            payments__status=PaymentStatus.COMPLETED
        ).distinct().count()

        inactive_users = total_users - active_users
        active_percentage = (active_users / total_users * 100) if total_users else 0.0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "active_percentage": round(active_percentage, 2)
        }
    
    @classmethod
    def users_without_payment(cls):
        return cls.objects.exclude(
            pk__in=Payment.objects.values_list('user_id', flat=True)
        )
    
    @classmethod
    def conference_payment_report(cls, conference: Conference, status: str = None, category: str = None):
        filters = Q(conference=conference)
        
        if status:
            filters &= Q(status=status)
        
        if category:
            if category == PaymentCategory.ABSTRACT.value:
                filters &= Q(abstract__isnull=False)
            elif category == PaymentCategory.JOIN_REQUEST.value:
                filters &= Q(abstract__isnull=True)
        
        return cls.objects.filter(filters).order_by('-timestamp')
    
    @classmethod
    def has_pending_payment(cls, user: User, conference: Conference) -> bool:
        return cls.objects.filter(user=user, conference=conference, status=PaymentStatus.PENDING.value).exists()
    
    @classmethod
    def get_payment(cls, user: User, conference: Conference):
        return cls.objects.filter(user=user, conference=conference).order_by("-timestamp").first()
    
    @classmethod
    def get_join_request_payments(cls):
        return cls.objects.filter(status=PaymentStatus.PENDING.value, abstract__isnull=True)
    
    @classmethod
    def filter_payment(cls, conference: Conference, search_query: str = None, status: str = None):
        filters = Q(conference=conference)
        
        if status and status != "All":
            filters &= Q(status=status)
        
        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(user__first_name__icontains=search_query) |
                Q(user__middle_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )
        return cls.objects.filter(filters).order_by('-timestamp')
    
    @classmethod
    def get_approved(cls, conference: Conference, search_query: str = None):
        filters = Q(status=PaymentStatus.COMPLETED.value, conference=conference)
        
        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(user__first_name__icontains=search_query) |
                Q(user__middle_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )
        return cls.objects.filter(filters).order_by('-timestamp')
    
    @classmethod
    def get_pending(cls, conference: Conference, search_query: str = None):
        filters = Q(status=PaymentStatus.PENDING.value, conference=conference)
        
        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(user__first_name__icontains=search_query) |
                Q(user__middle_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )
        return cls.objects.filter(filters).order_by('-timestamp')
    
    @classmethod
    def conference_payment_stats(cls, conference: Conference) -> Tuple[int, int, int, int]:
        payments = cls.objects.filter(conference=conference)
        
        total_payments = payments.count()
        join_requests = payments.filter(abstract__isnull=True)
        total_join_requests = join_requests.count()
        total_pending_join_requests = join_requests.filter(status=PaymentStatus.PENDING.value).count()
        total_abstract_payments = total_payments - total_join_requests
        
        return total_payments, total_join_requests, total_pending_join_requests, total_abstract_payments
    
    @classmethod
    def create_payment(
        cls,
        user: User,
        conference: Conference,
        amount: Decimal,
        payment_slip,
        abstract: Abstract = None,
    ):
        payment = cls(
            user=user,
            abstract=abstract,
            conference=conference,
            amount=amount,
            payment_slip=payment_slip
        )
        
        payment.save()
    
    @classmethod
    def get_payment_by_abstract_payment(cls, abstract: Abstract):
        return cls.objects.filter(abstract=abstract)
    
    @classmethod
    def mark_as_rejected(cls, payment_id: uuid.UUID, comment: str = None):
        """Reject a payment by its ID with an optional comment."""
        payment = cls.objects.filter(payment_id=payment_id).first()
        if payment and payment.status == PaymentStatus.PENDING.value:
            payment.status = PaymentStatus.REJECTED.value
            payment.comment = comment
            payment.save(update_fields=["status", "comment"])
            return payment
        return None

    @classmethod
    def mark_as_approved(cls, payment_id: uuid.UUID):
        """Mark a payment as approved."""
        payment = cls.objects.filter(payment_id=payment_id).first()
        if payment and payment.status == PaymentStatus.PENDING.value:
            payment.status = PaymentStatus.COMPLETED.value
            payment.save(update_fields=["status"])
            return payment
        return None

