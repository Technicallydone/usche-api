from django.contrib import admin
from .models import Settings

class SettingsAdmin(admin.ModelAdmin):
    list_display = ('phone_support', 'email_support')
    list_display_links = ('phone_support',)  # Set the field that can be clicked to edit
    search_fields = ('phone_support', 'email_support')
    list_filter = ('phone_support',)
    ordering = ('phone_support',)
    fieldsets = (
        (None, {
            'fields': ('phone_support', 'email_support')
        }),
    )
    list_editable = ('email_support',)  # Only make email_support editable
    readonly_fields = ('setting_id',)

admin.site.register(Settings, SettingsAdmin)
