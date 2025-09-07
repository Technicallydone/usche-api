from django.contrib import admin

from feedback.models import FeedbackAnswer

@admin.register(FeedbackAnswer)
class FeedbackAnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "option", "text", "submitted_at")
    list_filter = ("question", "submitted_at")
    search_fields = ("text",)
