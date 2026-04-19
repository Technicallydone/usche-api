from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path, include

router = DefaultRouter()

router.register(r'', views.SpeakerViewSet, basename='speakers')
router.register(r'images', views.SpeakerImageViewSet, basename='speaker-images')

urlpatterns = [
    path('', include(router.urls)),
]
 