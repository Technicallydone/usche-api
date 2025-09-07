from django.contrib import admin
from django.utils.html import format_html

from certificate.model.certificate_model import Certificate

class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        'certificate_id', 'user', 'conference', 
        'issued_at', 'is_sent', 'view_certificate'
    )
    search_fields = ('user__email', 'conference__conference_name')
    list_filter = ('is_sent', 'conference')
    ordering = ('-issued_at',)
    
    list_editable = ('is_sent',)
    readonly_fields = ('issued_at',)

    def view_certificate(self, obj):
        return format_html(
            '<a href="/admin/certificate/certificate/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.certificate_id
        )
    view_certificate.short_description = "Details"

admin.site.register(Certificate, CertificateAdmin)
