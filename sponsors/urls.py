from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path, include

router = DefaultRouter()

router.register(r'logo', views.SponsorLogoViewSet, basename='sponsors-logo')
router.register(r'', views.SponsorViewSet, basename='sponsors')

urlpatterns = [
    path('', include(router.urls)),
]
 