from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MyPharmacyProfileView, MedicineViewSet, ReceivePrescriptionView,
    MedicineOrderViewSet, PendingPrescriptionsView,
)

app_name = 'pharmacy'

router = DefaultRouter()
router.register('medicines', MedicineViewSet, basename='medicine')
router.register('orders', MedicineOrderViewSet, basename='order')

urlpatterns = [
    path('me/', MyPharmacyProfileView.as_view(), name='my_profile'),
    path('prescriptions/pending/', PendingPrescriptionsView.as_view(), name='pending_prescriptions'),
    path('prescriptions/<uuid:prescription_id>/receive/', ReceivePrescriptionView.as_view(), name='receive_prescription'),
    path('', include(router.urls)),
]
