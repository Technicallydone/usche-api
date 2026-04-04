from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'', views.ConferenceViewSet, basename='conference')
router.register(r'stats', views.ConferenceStatsViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]