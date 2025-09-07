from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'invitations', views.InvitationViewSet, basename='invitation')
urlpatterns = router.urls
 