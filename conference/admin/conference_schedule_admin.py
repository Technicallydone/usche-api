from django.contrib import admin
from django.utils.html import format_html

from conference.model.schedule_day import ScheduleDay
from conference.model.conference_schedule import ConferenceSchedule


class ConferenceScheduleInline(admin.TabularInline):
    model = ConferenceSchedule
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('date', 'start_time', 'end_time', 'activity', 'speaker', 'moderator', 'hall', 'session_type')
    ordering = ('start_time',)


@admin.register(ScheduleDay)
class ScheduleDayAdmin(admin.ModelAdmin):
    list_display = ('conference', 'title', 'date', 'location')
    list_filter = ('conference', 'date')
    search_fields = ('title', 'conference__conference_name')
    inlines = [ConferenceScheduleInline]
    ordering = ('date',)


@admin.register(ConferenceSchedule)
class ConferenceScheduleAdmin(admin.ModelAdmin):
    list_display = ('activity', 'schedule_day', 'date', 'start_time', 'end_time', 'session_type', 'view_edit')
    list_filter = ('session_type', 'date', 'schedule_day__conference')
    search_fields = ('activity', 'speaker', 'moderator', 'hall')
    ordering = ('date', 'start_time')

    def view_edit(self, obj):
        return format_html(
            '<a href="/admin/conference/conferenceschedule/{}/change/" class="button" '
            'style="padding:4px 8px; background:#3498db; color:#fff; border-radius:5px;">Edit</a>',
            obj.schedule_id 
        )

    view_edit.short_description = "Actions"
