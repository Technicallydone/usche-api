from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction

from conference.models import ConferenceScheduleDocument


class ConferenceScheduleDocumentForm(forms.ModelForm):
    class Meta:
        model = ConferenceScheduleDocument
        fields = '__all__'

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and not file.name.lower().endswith('.pdf'):
            raise forms.ValidationError("Only PDF files are allowed.")
        return file


class ConferenceScheduleDocumentAdmin(admin.ModelAdmin):
    form = ConferenceScheduleDocumentForm
    list_display = ('title', 'conference', 'is_active', 'uploaded_at', 'view_document')
    search_fields = ('title', 'conference__conference_name')
    list_filter = ('conference', 'is_active')
    list_editable = ('is_active',)
    ordering = ('-uploaded_at',)

    def view_document(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" class="button" '
                'style="padding:5px 10px; background:#2ecc71; color:#fff; border-radius:5px;">View PDF</a>',
                obj.file.url
            )
        return "-"
    view_document.short_description = "Document"

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if obj.is_active:
                ConferenceScheduleDocument.objects.filter(
                    conference=obj.conference,
                    is_active=True
                ).exclude(pk=obj.pk).update(is_active=False)
            super().save_model(request, obj, form, change)


admin.site.register(ConferenceScheduleDocument, ConferenceScheduleDocumentAdmin)
