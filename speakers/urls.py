from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'Speakers', views.SpeakerViewSet, basename='speaker')
urlpatterns = router.urls
 