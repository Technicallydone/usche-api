from django.contrib import admin

from feedback.model.feedback_email_log import FeedbackEmailLog

@admin.register(FeedbackEmailLog)
class FeedbackEmailLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'conference', 'sent_at')
    list_filter = ('conference', 'sent_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'conference__conference_name')
    ordering = ('-sent_at',)
