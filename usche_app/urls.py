
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/accounts/', include('user.urls')),
    path('api/v1/conference/', include('conference.urls')),
    path('api/v1/speaker/', include('speakers.urls')),
    path('api/v1/sponsor/', include('sponsors.urls')),
    path('api/v1/abstract/', include('abstracts.urls')),
    path('api/v1/payment/', include('payment.urls')),
    path('api/v1/attendee/', include('attendee.urls')),
    path('api/v1/invitation/', include('invitation.urls')),
    path('api/v1/certificate/', include('certificate.urls')),
    path('api/v1/feedback/', include('feedback.urls')),
    
]


admin.site.site_header = "USChe Administration"
admin.site.site_title = "USCHe"
admin.site.index_title = "USCHe"