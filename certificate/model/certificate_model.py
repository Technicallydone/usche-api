import uuid
from django.db import models
from django.utils import timezone
from user.models import User
from conference.models import Conference
from django.db.models import Value
from django.db.models.functions import Concat, Lower

class Certificate(models.Model):
    certificate_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='certificates', null=True, blank=True)
    
    issued_at = models.DateTimeField(default=timezone.now, editable=False)
    is_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'certificate'
        app_label = 'certificate'
        unique_together = ('user', 'conference')

    def __str__(self):
        return f"Certificate for {self.user.email} - {self.conference.conference_name}"
    
    @classmethod
    def certificates_by_conference_with_search(cls, conference_id: uuid.UUID, search: str = None):
        queryset = cls.objects.filter(
            conference_id=conference_id
        ).select_related("user").order_by('-issued_at')

        if search:
            search = search.lower()
            queryset = queryset.annotate(
                search_full_name=Lower(
                    Concat(
                        'user__first_name',
                        Value(' '),
                        'user__middle_name',
                        Value(' '),
                        'user__last_name'
                    )
                )
            ).filter(search_full_name__icontains=search)
            
        queryset = queryset.filter(user__is_superuser=False)

        return queryset

    
    @classmethod
    def users_without_certificate_for_conference(cls, conference: Conference, search: str = None):
        from user.models import User

        queryset = User.objects.exclude(
            user_id__in=cls.objects.filter(conference=conference).values('user_id')
        ).filter(is_superuser=False)

        if search:
            search = search.lower()
            queryset = queryset.annotate(
                search_full_name=Lower(
                    Concat(
                        'first_name',
                        Value(' '),
                        'middle_name',
                        Value(' '),
                        'last_name'
                    )
                )
            ).filter(search_full_name__icontains=search)

        return queryset


