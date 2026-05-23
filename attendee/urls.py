from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()

router.register(r'', views.AttendeeViewSet, basename='attendees')
# router.register(r'attendees', views.AttendeeReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
 