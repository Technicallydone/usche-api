import uuid
from django.db import models
from django.core.validators import EmailValidator 

from utils.validator import validate_phone_number 

class Settings(models.Model):
    setting_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_support = models.CharField(max_length=50, null=True, blank=True, validators=[validate_phone_number])
    email_support = models.CharField(max_length=100, null=False, blank=False, validators=[EmailValidator()]) 
    
    class Meta:
        db_table = 'app_settings'
        app_label = 'settings'
        
    @classmethod
    def get_contact_support(cls):
        return cls.objects.filter().first()
    
