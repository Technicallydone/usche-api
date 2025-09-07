from django.contrib import admin
from django.utils.html import format_html

from conference.models import BankAccount


class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'account_number', 'bank_name', 'currency', 'view_details')
    search_fields = ('account_name', 'account_number', 'bank_name')
    list_filter = ('bank_name', 'currency')
    ordering = ('account_name',)

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/conference/bankaccount/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.account_id
        )

    view_details.short_description = "Actions"

admin.site.register(BankAccount, BankAccountAdmin)
