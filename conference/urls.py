from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# router.register(r'stats', views.ConferenceStatsViewSet, basename='stats')
router.register(r'', views.ConferenceViewSet, basename='conference')

urlpatterns = [
    path('', include(router.urls)),
]