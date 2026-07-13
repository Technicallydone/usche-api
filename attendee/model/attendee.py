import uuid
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from attendee.enums.attendee_status import AttendeeStatus
from conference.models import Conference
from user.models import User


class Attendee(models.Model):
    attendee_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="attendees")
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attended_conferences")
    invitation_sent = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=AttendeeStatus.choices(),
        default=AttendeeStatus.default(),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendees'
        app_label = 'attendee'

    def __str__(self):
        return f"{self.participant.full_name} attends {self.conference.conference_name}"

    def update_status_to_active(self):
        """Updates the status of an attendee to ACTIVE."""
        self.status = AttendeeStatus.ACTIVE.value
        self.save(update_fields=["status"])
        

    def update_status_to_cancelled(self):
        """Updates the status of an attendee to CANCELLED."""
        self.status = AttendeeStatus.CANCELLED.value
        self.save(update_fields=["status"])
        

    def update_status_to_waiting(self):
        """Updates the status of an attendee to WAITING."""
        self.status = AttendeeStatus.WAITING.value
        self.save(update_fields=["status"])
        

    def update_status_to_attended(self):
        """Updates the status of an attendee to ATTENDED."""
        self.status = AttendeeStatus.ATTENDED.value
        self.save(update_fields=["status"])
        

    def update_status(self, status: str):
        """Updates the status of an attendee to a given status."""
        if not AttendeeStatus.validate(status):
            raise ValueError(f"Invalid status: {status}")
        self.status = status
        self.save(update_fields=["status"])
        
    def mark_invitation_sent(self):
        """Marks the invitation as sent."""
        self.invitation_sent = True
        self.save(update_fields=["invitation_sent"])
        
    @classmethod
    def conference_attendee_report(cls, conference: Conference):
        return cls.objects.filter(conference=conference)
        
    @classmethod
    def total_conference_attendees(cls, conference: Conference) -> int:
        return cls.objects.filter(conference=conference).count()
    
    @classmethod
    def create_attendee(cls, conference: Conference, participant: User):
        """Creates and saves an attendee with ACTIVE status if not already existing."""
        if cls.objects.filter(conference=conference, participant=participant).exists():
            raise ValidationError(
                f"Attendee for participant {participant} already exists for conference {conference}."
            )
        attendee = cls.objects.create(
            conference=conference,
            participant=participant,
            status=AttendeeStatus.ACTIVE.value
        )
        return attendee

    @classmethod
    def get_attendee(cls, conference: Conference, participant: User):
        """Fetches an existing attendee based on conference and participant."""
        return cls.objects.filter(conference=conference, participant=participant).first()
    
    @classmethod
    def get_attendee_by_id(cls, attendee_id: uuid.UUID):
        """Fetches an existing attendee based on conference and participant."""
        return cls.objects.filter(attendee_id=attendee_id).first()
    
    @classmethod
    def get_attendee(cls, participant: User, conference: Conference):
        return cls.objects.filter(participant=participant, conference=conference).first()
    
    @classmethod
    def get_attendees_by_ids(cls, attendee_ids):
        """Get attendees by a list of IDs."""
        return cls.objects.filter(attendee_id__in=attendee_ids)
    
    @classmethod
    def filter_attendees(
        cls,
        search_query: str = None,
        conference_id: str = None,
        created_from=None,
        created_to=None,
        attendee_status = None
    ):
        filters = Q(participant__is_superuser=False)

        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(participant__first_name__icontains=search_query) |
                Q(participant__middle_name__icontains=search_query) |
                Q(participant__last_name__icontains=search_query)
            )
        
        if attendee_status:
            filters &= Q(status=attendee_status)

        if conference_id:
            filters &= Q(conference__conference_id=conference_id)

        if created_from:
            filters &= Q(created_at__date__gte=created_from)

        if created_to:
            filters &= Q(created_at__date__lte=created_to)
        
        return (
            cls.objects
            .filter(filters)
            .select_related("participant", "conference")
            .order_by("-created_at")
        )
        
    @classmethod
    def get_conference_attendees(cls, conference: Conference, search_query: str = None):
        
        filters = Q(
            conference=conference
        )
        
        if search_query:
            search_query = search_query.lower()
            filters &= (
                Q(participant__first_name__icontains=search_query) |
                Q(participant__middle_name__icontains=search_query) |
                Q(participant__last_name__icontains=search_query)
            )

        return cls.objects.filter(filters)
