from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'attendees', views.AttendeeViewSet, basename='attendee')
router.register(r'attendees', views.AttendeeReportViewSet, basename='report')

urlpatterns = router.urls
 