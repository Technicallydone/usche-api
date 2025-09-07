from typing import List, Optional
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings

from conference.models import Conference
from user.enums.invitation_status import InvitationStatusEnum
from user.enums.role import ROLE
from user.models import User 
from django.db.models import Q, QuerySet

class Invitation(models.Model):
    invitation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invitations")
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="invitations")
    invitation_sent = models.BooleanField(default=False)
    invited_on = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'invitation'
        app_label = 'invitation'
        
    def __str__(self):
        return f"Invitation for {self.user} to {self.conference}"
    
    def mark_invitation_sent(self):
        self.invitation_sent = True
        self.save(update_fields=["invitation_sent"])
        
    @classmethod
    def get_conference_invitation(cls, conference: Conference) -> 'Invitation':
        return cls.objects.filter(conference=conference, invitation_sent=False).order_by('-invited_on').first()
        
    @classmethod
    def add_users(cls, users: List[User], conference: Conference) -> 'QuerySet[Invitation]':
        """
        Adds a list of users to a conference by creating invitations, skipping users
        who are already invited to that conference.
        """
        invitations = []
        existing_invitations = cls.objects.filter(conference=conference, user__in=users)

        users_to_invite = [user for user in users if user not in existing_invitations.values_list('user', flat=True)]
        
        for user in users_to_invite:
            invitation = cls.objects.create(user=user, conference=conference)
            invitations.append(invitation)

        return invitations

    @classmethod
    def filter_users(cls, conference: Conference, filter_type: str = InvitationStatusEnum.ALL.value, search_query: Optional[str] = None):
        """
        Filters users based on the type of filter (ALL, INVITED, NOT_INVITED, INVITED_NOT_SENT)
        """
        filter_type = InvitationStatusEnum.validate(filter_type)

        filters = Q(is_superuser=False, is_active=True)
        filters &= ~Q(role=ROLE.ADMIN.value)
        
        invitation_filters = Q(conference=conference)

        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        if filter_type == InvitationStatusEnum.ALL.value:
            users = User.objects.filter(filters)
            invitations = cls.objects.filter(invitation_filters)
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
            invited_users = User.objects.filter(filters, invitations__isnull=False).distinct()
            return [{'user': user, 'invitation_status': True, 'invitation_sent': user.invitations.first().invitation_sent} for user in invited_users]

        elif filter_type == InvitationStatusEnum.NOT_INVITED.value:
            not_invited_users = User.objects.filter(filters, invitations__isnull=True)
            return [{'user': user, 'invitation_status': False, 'invitation_sent': False} for user in not_invited_users]

        elif filter_type == InvitationStatusEnum.INVITED_NOT_SENT.value:
            invited_not_sent_users = User.objects.filter(filters, invitations__invitation_sent=False)
            return [{'user': user, 'invitation_status': True, 'invitation_sent': False} for user in invited_not_sent_users]

        else:
            raise ValueError("Invalid filter_type. Must be one of: 'ALL', 'INVITED', 'NOT_INVITED', 'INVITED_NOT_SENT'.")
