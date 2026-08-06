
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/accounts/', include('user.urls')),
    path('api/v1/conference/', include('conference.urls')),
    path('api/v1/speaker/', include('speakers.urls')),
    path('api/v1/sponsors/', include('sponsors.urls')),
    path('api/v1/themes/', include('themes.urls')),
    path('api/v1/abstracts/', include('abstracts.urls')),
    path('api/v1/payments/', include('payment.urls')),
    path('api/v1/attendees/', include('attendee.urls')),
    path('api/v1/invitations/', include('invitation.urls')),
    path('api/v1/certificates/', include('certificate.urls')),
    path('api/v1/feedback/', include('feedback.urls')),
    path('api/v1/badges/', include('badge.urls')),
    
]


admin.site.site_header = "USChe Administration"
admin.site.site_title = "USCHe"
admin.site.index_title = "USCHe"