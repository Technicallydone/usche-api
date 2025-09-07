from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'feedback', views.ConferenceQuestionViewSet, basename='feedback')
router.register(r'feedback-report', views.FeedbackReportViewSet, basename='feedback-report')

urlpatterns = router.urls
 