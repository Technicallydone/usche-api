from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'', views.PaymentViewSet, basename='payments')
# router.register(r'payments', views.ConferencePaymentReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
