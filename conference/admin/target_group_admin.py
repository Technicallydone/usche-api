from django.contrib import admin
from django.utils.html import format_html

from conference.models import TargetGroup

class TargetGroupAdmin(admin.ModelAdmin):
    list_display = ('conference', 'group_name', 'view_details')
    search_fields = ('conference__conference_name', 'group_name')
    list_filter = ('conference',)
    ordering = ('conference', 'group_name')

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/conference/targetgroup/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.pk
        )

    view_details.short_description = "Actions"

admin.site.register(TargetGroup, TargetGroupAdmin)
