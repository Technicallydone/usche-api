import uuid
from django.db import models
from conference.model.conference import Conference
from utils.image_validator import validate_image
from utils.upload_image import upload_slider_to


class PreConferenceSlider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        related_name="pre_conference_sliders"
    )

    image = models.ImageField(upload_to=upload_slider_to, validators=[validate_image])

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pre_conference_sliders"
        app_label = 'conference'

    def __str__(self):
        return f"Pre Conference Slider - {self.conference.conference_name}"

    def toggle_active(self):
        self.is_active = not self.is_active
        self.save(update_fields=["is_active"])
        return self.is_active