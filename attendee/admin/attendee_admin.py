from django.contrib import admin
from django.utils.html import format_html
from attendee.models import Attendee


class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('participant_link', 'conference_link', 'status', 'invitation_sent', 'view_details')
    search_fields = (
        'participant__first_name',
        'participant__middle_name',
        'participant__last_name',
        'participant__email',
        'conference__conference_name',
    )
    list_filter = ('conference', 'status', 'invitation_sent')
    ordering = ('conference',)

    def participant_link(self, obj):
        return format_html(
            '<a href="/admin/user/user/{}/change/" style="color: #3498db;">{}</a>',
            obj.participant.pk,
            obj.participant.full_name if obj.participant.full_name else obj.participant.email
        )

    participant_link.short_description = "Participant"

    def conference_link(self, obj):
        return format_html(
            '<a href="/admin/conference/conference/{}/change/" style="color: #3498db;">{}</a>',
            obj.conference.pk,
            obj.conference.conference_name
        )

    conference_link.short_description = "Conference"

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/attendee/attendee/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.pk
        )

    view_details.short_description = "Actions"

    list_editable = ('status', 'invitation_sent')

    fieldsets = (
        (None, {'fields': ('conference', 'participant', 'status', 'invitation_sent')}),
    )


admin.site.register(Attendee, AttendeeAdmin)
