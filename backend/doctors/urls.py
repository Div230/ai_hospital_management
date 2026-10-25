from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DoctorSlotsView, MyDoctorProfileView, DoctorListView, DoctorAvailabilityViewSet,
    DoctorPatientListView, ClinicalNoteViewSet,
)

app_name = 'doctors'

router = DefaultRouter()
router.register('availability', DoctorAvailabilityViewSet, basename='availability')
router.register('clinical-notes', ClinicalNoteViewSet, basename='clinical-note')

urlpatterns = [
    path('me/', MyDoctorProfileView.as_view(), name='my_profile'),
    path('<uuid:pk>/slots/', DoctorSlotsView.as_view(), name='doctor_slots'),
    path('directory/', DoctorListView.as_view(), name='directory'),
    path('my-patients/', DoctorPatientListView.as_view(), name='my_patients'),
    path('', include(router.urls)),
]
