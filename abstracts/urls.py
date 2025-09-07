from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'abstracts', views.AbstractViewSet, basename='abstract')
router.register(r'abstracts', views.OrganizerAbstractViewSet, basename='organizer')
router.register(r'abstracts', views.AbstractReportViewSet, basename='report')


urlpatterns = router.urls
 