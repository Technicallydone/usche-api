from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'payments', views.ConferencePaymentReportViewSet, basename='report')


urlpatterns = router.urls
