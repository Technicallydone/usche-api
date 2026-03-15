import uuid
from django.db import models
from conference.model.conference import Conference


class RegistrationFee(models.Model):
    fee_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        related_name="registration_fees"
    )

    category = models.CharField(max_length=255, null=False, blank=False)

    early_bird_fee = models.CharField(max_length=100, null=False, blank=False)
    late_registration_fee = models.CharField(max_length=100, null=False, blank=False)

    class Meta:
        db_table = 'registration_fee'
        app_label = 'conference'

    def __str__(self):
        return f"{self.category} - Early Bird: {self.early_bird_fee} Late Registration: {self.late_registration_fee}"