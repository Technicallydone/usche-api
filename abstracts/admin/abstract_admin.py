from django.contrib import admin
from django.utils.html import format_html
from abstracts.models import Abstract


class AbstractAdmin(admin.ModelAdmin):
    list_display = ('title', 'authors', 'user_link', 'sub_theme_link', 'status', 'is_payment_done', 'view_details')
    search_fields = ('title', 'user__first_name', 'user__last_name', 'sub_theme__title', 'status')
    list_filter = ('sub_theme', 'status', 'is_payment_done')
    ordering = ('-created_at',)

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/user/user/{}/change/" style="color: #3498db;">{}</a>',
            obj.user.pk,
            obj.user.full_name if obj.user.full_name else obj.user.email
        )

    user_link.short_description = "User"

    def sub_theme_link(self, obj):
        return format_html(
            '<a href="/admin/theme/subtheme/{}/change/" style="color: #3498db;">{}</a>',
            obj.sub_theme.pk,
            obj.sub_theme.title
        )

    sub_theme_link.short_description = "Sub Theme"

    def view_details(self, obj):
        return format_html(
            '<a href="/admin/abstracts/abstract/{}/change/" class="button" '
            'style="padding:5px 10px; background:#3498db; color:#fff; border-radius:5px;">View</a>',
            obj.pk
        )

    view_details.short_description = "Actions"

    list_editable = ('status', 'is_payment_done')

    list_filter = ('sub_theme', 'status', 'is_payment_done')

    fieldsets = (
        (None, {'fields': ('title', 'sub_theme', 'user', 'document', 'keywords', 'authors', 'content')}),
        ('Review Details', {'fields': ('status', 'is_payment_done', 'comment')}),
    )


admin.site.register(Abstract, AbstractAdmin)
