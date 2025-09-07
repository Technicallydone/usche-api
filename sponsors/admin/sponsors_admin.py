from django.contrib import admin
from django.utils.html import format_html
from sponsors.models import Sponsor

class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'conference_link', 'website_link', 'contact_email', 'priority', 'view_details')
    search_fields = ('name', 'conference__conference_name', 'contact_email')
    list_filter = ('conference',)
    ordering = ('priority',)
    list_editable = ('priority',)

    def conference_link(self, obj):
        # Generates a clickable link to the conference admin page
        return format_html(
            '<a href="/admin/conference/conference/{}/change/" style="color: #3498db;">{}</a>',
            obj.conference.pk,
            obj.conference.conference_name
        )

    conference_link.short_description = "Conference"

    def website_link(self, obj):
        # Generates a clickable link to the sponsor's website
        if obj.website:
            return format_html('<a href="{}" target="_blank" style="color: #3498db;">Visit Website</a>', obj.website)
        return "-"

    website_link.short_description = "Website"

    def view_details(self, obj):
        # Generates a "View" button that links to the sponsor detail page
        return format_html(
            '<a href="/admin/sponsors/sponsor/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.pk
        )

    view_details.short_description = "Actions"

admin.site.register(Sponsor, SponsorAdmin)
