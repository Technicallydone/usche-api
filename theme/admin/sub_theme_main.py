from django.contrib import admin
from django.utils.html import format_html
from theme.models import SubTheme

class SubThemeAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme_link', 'view_details')
    search_fields = ('title', 'theme__title')
    list_filter = ('theme',)
    ordering = ('theme', 'title')

    def theme_link(self, obj):
        return format_html(
            '<a href="/admin/theme/maintheme/{}/change/" class="button" '
            'style="padding: 5px 10px; background-color: #3498db; color: white; '
            'border-radius: 5px; text-decoration: none;">{}</a>',
            obj.theme.pk,
            obj.theme.title
        )

    theme_link.short_description = "Main Theme"

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/theme/subtheme/{}/change/" class="button" '
            'style="padding: 5px 10px; background-color: #3498db; color: white; '
            'border-radius: 5px; text-decoration: none;">View</a>',
            obj.pk
        )

    view_details.short_description = "Actions"

admin.site.register(SubTheme, SubThemeAdmin)
