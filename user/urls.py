from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'users', views.UserViewSet, basename='user')
router.register(r'access/roles', views.AppRoleViewSet, basename='approle')
router.register(r'access/permissions', views.AppPermissionViewSet, basename='apppermission')

urlpatterns = [
    path('', include(router.urls)),
]
 