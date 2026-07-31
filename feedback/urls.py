from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FeedbackQuestionViewSet

router = DefaultRouter()

router.register(
    r"",
    FeedbackQuestionViewSet,
    basename="feedback",
)

urlpatterns = [
    path("", include(router.urls)),
]