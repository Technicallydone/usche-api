import uuid
from django.db import models

from conference.model.conference import Conference

class BankAccount(models.Model):
    account_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="bank_accounts", null=True, blank=True)
    
    account_name = models.CharField(max_length=255, null=False, blank=False)
    account_number = models.CharField(max_length=50, null=False, blank=False)
    bank_name = models.CharField(max_length=255, null=False, blank=False)
    currency = models.CharField(max_length=50, null=False, blank=False) 
    bank_code = models.CharField(max_length=10, null=False, blank=False)
    swift_code = models.CharField(max_length=20, null=False, blank=False)

    class Meta:
        db_table = 'bank_accounts'
        app_label = 'conference'

    def __str__(self):
        return f"{self.account_name} - {self.bank_name}"
