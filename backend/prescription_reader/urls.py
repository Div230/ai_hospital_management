from rest_framework.routers import DefaultRouter
from .views import PrescriptionReaderViewSet

router = DefaultRouter()
router.register('', PrescriptionReaderViewSet, basename='prescription-reader')
urlpatterns = router.urls
