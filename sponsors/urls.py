from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'sponsors', views.SponsorViewSet, basename='sponsor')
urlpatterns = router.urls
 