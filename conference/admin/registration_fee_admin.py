from django.contrib import admin
from django.utils.html import format_html

from conference.models import RegistrationFee

class RegistrationFeeAdmin(admin.ModelAdmin):
    list_display = ('conference', 'category', 'early_bird_fee', 'late_registration_fee', 'view_details')
    search_fields = ('conference__conference_name', 'category')
    list_filter = ('conference',)
    ordering = ('conference', 'category')

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/conference/registrationfee/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.pk
        )

    view_details.short_description = "Actions"

admin.site.register(RegistrationFee, RegistrationFeeAdmin)
