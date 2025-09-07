from django.contrib import admin
from django.utils.html import format_html
from payment.models import Payment

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'payment_for', 'amount', 'status', 'timestamp',)
    search_fields = ('user__first_name', 'user__last_name', 'abstract__title',)
    list_filter = ('status',)
    ordering = ('-timestamp',)
    list_editable = ('status',) 

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/user/user/{}/change/" style="color: #3498db;">{}</a>',
            obj.user.pk,
            obj.user.full_name if obj.user.full_name else obj.user.email
        )
    
    user_link.short_description = "User"

    def payment_for(self, obj):
        if obj.abstract:
            return format_html(
                '<a href="/admin/abstracts/abstract/{}/change/" style="color: #3498db;">Abstract: {}</a>',
                obj.abstract.pk, obj.abstract.title
            )
        return "N/A"

    payment_for.short_description = "Payment For"

    fieldsets = (
        (None, {'fields': ('user', 'amount', 'payment_slip', 'status',)}),
        ('Linked to', {'fields': ('abstract',)}),
    )


admin.site.register(Payment, PaymentAdmin)
