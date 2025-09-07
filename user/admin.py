from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from .models import User

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'phone_number', 'first_name', 'middle_name', 'last_name', 'country', 'affiliation', 'occupation', 'title', 'role')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm

    list_display = (
        'title', 'full_name', 'phone_number', 'email', 'country',
        'occupation', 'is_active', 'resend_activation_email',
        'created_at_display', 'view_details'
    )
    search_fields = ('email', 'phone_number', 'first_name', 'last_name')
    list_filter = ('is_active',)
    ordering = ()
    list_editable = ('is_active', 'resend_activation_email',)
    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'middle_name', 'last_name', 'country',
                'affiliation', 'occupation', 'title'
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_superuser', 'is_staff', 'role', 'groups')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'phone_number', 'first_name', 'middle_name', 'last_name',
                'country', 'affiliation', 'occupation', 'title',
                'role', 'password1', 'password2'
            ),
        }),
    )
    readonly_fields = ('is_superuser',)
    list_per_page = 20

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "Full Name"

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/user/user/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.user_id
        )
    view_details.short_description = "Actions"

    def created_at_display(self, obj):
        return obj.created_at.strftime('%b %d, %Y at %I:%M %p')
    created_at_display.short_description = "Created At"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(is_superuser=False).order_by('-created_at')

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly_fields += ['role']
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)
