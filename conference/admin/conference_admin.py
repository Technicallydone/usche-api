from django.contrib import admin
from django.utils.html import format_html
from django import forms
from conference.model.conference import Conference 

class ConferenceAdminForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass


class ConferenceAdmin(admin.ModelAdmin):
    form = ConferenceAdminForm 

    list_display = (
        'conference_name',
        'start_date',
        'end_date',
        'venue_name',
        'capacity',
        'registration_open',
        'abstract_submission_deadline',
        'listing_date',
        'updated_at',
        'view_details',
        'generate_qr_code'
    )
    list_filter = ('registration_open', 'start_date', 'end_date')
    search_fields = ('conference_name', 'venue_name', 'description')
    date_hierarchy = 'start_date'
    
    readonly_fields = (
        'conference_id', 
        'listing_date', 
        'updated_at',
    )

    fieldsets = (
        (None, {
            'fields': (
                'conference_name',
                'description',
                'certificate_background'
            )
        }),
        ('Dates and Times', {
            'fields': (
                'start_date',
                'end_date',
                'start_time',
                'end_time',
                'abstract_submission_deadline'
            )
        }),
        ('Venue Information', {
            'fields': (
                'venue_name',
                'venue_website',
                'venue_description',
                'venue_directions',
                'capacity'
            )
        }),
        ('Status', {
            'fields': (
                'registration_open',
            )
        }),
        ('System Information', {
            'fields': (
                'conference_id',
                'listing_date',
                'updated_at'
            ),
            'classes': ('collapse',),
        }),
    )

    list_editable = ('registration_open',)

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/conference/conference/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.conference_id
        )
    view_details.short_description = "Details"

    def generate_qr_code(self, obj):
        return format_html(
            '<a href="/v1/conference/conferences/conference_schedule/{}/qr-code/" target="_blank" class="button" '
            'style="padding:5px 10px; background:#27ae60; color:#fff; border-radius:5px;">Generate QR</a>',
            obj.conference_id
        )
    generate_qr_code.short_description = "QR Code"

admin.site.register(Conference, ConferenceAdmin)