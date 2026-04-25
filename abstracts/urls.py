from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'', views.AbstractViewSet, basename='abstracts')
# router.register(r'abstracts', views.OrganizerAbstractViewSet, basename='organizer')
# router.register(r'abstracts', views.AbstractReportViewSet, basename='report')


urlpatterns = [
    path('', include(router.urls)),
]