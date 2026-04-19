from django.contrib import admin
from django.utils.html import format_html
from themes.models import MainTheme

class MainThemeAdmin(admin.ModelAdmin):
    list_display = ('title', 'conference_link', 'view_details')
    search_fields = ('title', 'conference__conference_name')
    list_filter = ('conference',)
    ordering = ('conference', 'title')

    def conference_link(self, obj):
        return format_html(
            '<a href="/admin/conference/conference/{}/change/" class="button" '
            'style="padding: 5px 10px; background-color: #3498db; color: white; '
            'border-radius: 5px; text-decoration: none;">{}</a>',
            obj.conference.pk,
            obj.conference.conference_name
        )

    conference_link.short_description = "Conference"

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/theme/maintheme/{}/change/" class="button" '
            'style="padding: 5px 10px; background-color: #3498db; color: white; '
            'border-radius: 5px; text-decoration: none;">View</a>',
            obj.pk
        )

    view_details.short_description = "Actions"

admin.site.register(MainTheme, MainThemeAdmin)
