
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title="USCHE API",
        default_version="v1",
        description="USCHE APP API documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="finesawa36@gmail.com"),
        license=openapi.License(name="MIT")
    ),
    public=True
)

urlpatterns = [
    path('', lambda request: redirect('/admin/')),
    path("admin/", admin.site.urls),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/user/', include('user.urls')),
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