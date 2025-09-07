import uuid
from django.db import models
from conference.models import Conference
from speakers.enum.speaker_enum import SPEAKER_CATEGORY, SPEAKER_TITLE
from utils.image_validator import validate_image
from utils.upload_image import upload_speakers_to

class Speaker(models.Model):
    speaker_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the speaker."
    )
    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        related_name="speakers",
        help_text="Select the conference this speaker belongs to."
    )
    speaker_category = models.CharField(
        max_length=255,
        choices=SPEAKER_CATEGORY.choices(),
        null=False,
        blank=True,
        help_text="Select the category of the speaker (Keynote, Plenary, Breakout)."
    )
    name = models.CharField(
        max_length=150,
        null=False,
        blank=False,
        help_text="Enter the full name of the speaker."
    )
    title = models.CharField(
        max_length=50,
        choices=SPEAKER_TITLE.choices(),
        null=True,
        blank=True,
        help_text="Select the speaker's title (e.g., Dr., Prof., Mr., Ms.)."
    )
    specialization = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Enter the speaker's area of expertise or specialization."
    )
    organization = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Enter the name of the speaker's organization or workplace."
    )
    role = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Enter the speaker's role or position (e.g., CEO, Lecturer)."
    )
    
    biography = models.TextField(
        null=False,
        blank=False,
        help_text="Enter the speaker's biography or bibliograph details."
    )

    speaker_image = models.ImageField(
        upload_to=upload_speakers_to,
        validators=[validate_image],
        null=True,
        blank=True,
        help_text="Upload a profile picture for the speaker in WebP format."
    )    
    
    class Meta:
        db_table = 'speakers'
        app_label = 'speakers'

    def __str__(self):
        return f"{self.title} {self.name} - {self.specialization}"

    @classmethod
    def get_speaker_by_id(cls, speaker_id: uuid.UUID):
        return cls.objects.filter(speaker_id=speaker_id).first()