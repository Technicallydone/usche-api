from rest_framework.routers import DefaultRouter
from .views import CertificateViewSet

router = DefaultRouter()

router.register(r'certificate', CertificateViewSet, basename='certificate')

urlpatterns = router.urls
