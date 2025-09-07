from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'conferences', views.ConferenceViewSet, basename='conference')
router.register(r'conferences', views.ConferenceStatsViewSet, basename='conference-stats')
urlpatterns = router.urls
 