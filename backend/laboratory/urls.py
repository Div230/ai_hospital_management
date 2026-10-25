from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyLabProfileView, LabTestRequestViewSet, UploadLabReportView, LaboratoryListView

app_name = 'laboratory'

router = DefaultRouter()
router.register('test-requests', LabTestRequestViewSet, basename='test-request')

urlpatterns = [
    path('me/', MyLabProfileView.as_view(), name='my_profile'),
    path('directory/', LaboratoryListView.as_view(), name='directory'),
    path('test-requests/<uuid:test_request_id>/upload-report/', UploadLabReportView.as_view(), name='upload_report'),
    path('', include(router.urls)),
]
