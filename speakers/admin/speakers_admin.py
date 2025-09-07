from django.contrib import admin
from django.utils.html import format_html

from speakers.models import Speaker
from conference.models import Conference

class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'conference_link', 'category', 'specialization', 'organization', 'role', 'view_details')
    search_fields = ('name', 'specialization', 'organization', 'role', 'conference__conference_name')
    list_filter = ('conference', 'speaker_category')
    ordering = ('conference', 'name')

    def conference_link(self, obj):
        # Generates a clickable link to the conference admin page
        return format_html(
            '<a href="/admin/conference/conference/{}/change/" style="color: #3498db;">{}</a>',
            obj.conference.pk,
            obj.conference.conference_name
        )

    conference_link.short_description = "Conference"

    def category(self, obj):
        return obj.get_speaker_category_display()

    category.short_description = "Category"

    def view_details(self, obj):
        # Generates a "View" button that links to the speaker detail page
        return format_html(
            '<a href="/admin/speakers/speaker/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.pk
        )

    view_details.short_description = "Actions"

admin.site.register(Speaker, SpeakerAdmin)
