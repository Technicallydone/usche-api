from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from invitation.models import Invitation

class InvitationAdmin(admin.ModelAdmin):
    list_display = ('invitation_id', 'get_user_full_name', 'get_conference_name', 'invitation_sent', 'invited_on', 'mark_sent_button')
    search_fields = ('user__first_name', 'user__last_name', 'conference__conference_name')
    list_filter = ('invitation_sent', 'invited_on')

    def get_queryset(self, request):
        """Exclude admin users (is_staff=True or is_superuser=True) from the invitation list."""
        queryset = super().get_queryset(request)
        # return queryset.exclude(user__is_staff=True).exclude(user__is_superuser=True)
        return queryset.exclude(user__is_superuser=True)
        

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_user_full_name.admin_order_field = 'user'
    get_user_full_name.short_description = 'User Name'

    def get_conference_name(self, obj):
        return obj.conference.conference_name
    get_conference_name.admin_order_field = 'conference'
    get_conference_name.short_description = 'Conference Name'

    def mark_sent_button(self, obj):
        url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[obj.pk])
        return format_html('<a class="button" href="{}">Mark as Sent</a>', url)
    mark_sent_button.short_description = 'Actions'

admin.site.register(Invitation, InvitationAdmin)
