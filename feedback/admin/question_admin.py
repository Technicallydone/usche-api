from django.contrib import admin
from django.utils.html import format_html
from feedback.models import Option, Question
from feedback.enums.question_type import QuestionTypeEnum


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    fields = ('option',)
    show_change_link = False
    classes = ['options-group']  # Added class for easier JavaScript targeting


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'type', 'conference', 'view_edit')
    list_filter = ('type', 'conference')
    search_fields = ('question', 'conference__conference_name')
    ordering = ('conference', 'id')
    
    class Media:
        js = ('admin/js/question_type_handler.js',)
        css = {
            'all': ('admin/css/question_admin.css',)
        }

    def get_inlines(self, request, obj=None):
        """
        Only show OptionInline if:
        - Creating a new question (let admin add options if they plan to set type to multiple-choice)
        - Or editing an existing multiple-choice question
        """
        if obj is None or obj.type == QuestionTypeEnum.MULTIPLE_CHOICE.value:
            return [OptionInline]
        return []

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Question Details', {
                'fields': ('conference', 'question', 'type'),
                'description': 'Note: Options are only available for multiple-choice questions'
            }),
        ]
        return fieldsets

    def save_model(self, request, obj, form, change):
        """
        Additional validation when saving the question
        """
        super().save_model(request, obj, form, change)
        
        # If changing to text type, delete existing options
        if obj.type == QuestionTypeEnum.TEXT.value:
            obj.options.all().delete()

    def view_edit(self, obj):
        return format_html(
            '<a href="/admin/{}/{}/{}/change/" class="button" '
            'style="padding:4px 8px; background:#3498db; color:#fff; border-radius:5px;">Edit</a>',
            obj._meta.app_label,
            obj._meta.model_name,
            obj.pk
        )
    view_edit.short_description = "Actions"


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'option')
    list_filter = ('question__conference', 'question')
    search_fields = ('option', 'question__question')
    ordering = ('question__conference', 'question__id')
    
    def get_queryset(self, request):
        """
        Only show options for multiple-choice questions
        """
        qs = super().get_queryset(request)
        return qs.filter(question__type=QuestionTypeEnum.MULTIPLE_CHOICE.value)