from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'auths', views.AuthenticationViewSet, basename='auth')
router.register(r'auths', views.SignOutViewSet, basename='sign-out')

urlpatterns = router.urls
