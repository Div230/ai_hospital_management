from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MyPatientProfileView, FamilyMemberViewSet, MedicalHistoryViewSet,
    MedicalReportViewSet, MedicineReminderViewSet, VaccinationReminderViewSet,
    TriggerSOSView, MySOSAlertsView, AmbulanceTrackingView,
)

app_name = 'patients'

router = DefaultRouter()
router.register('family-members', FamilyMemberViewSet, basename='family-member')
router.register('medical-history', MedicalHistoryViewSet, basename='medical-history')
router.register('medical-reports', MedicalReportViewSet, basename='medical-report')
router.register('medicine-reminders', MedicineReminderViewSet, basename='medicine-reminder')
router.register('vaccination-reminders', VaccinationReminderViewSet, basename='vaccination-reminder')

urlpatterns = [
    path('me/', MyPatientProfileView.as_view(), name='my_profile'),
    path('sos/trigger/', TriggerSOSView.as_view(), name='sos_trigger'),
    path('sos/my-alerts/', MySOSAlertsView.as_view(), name='sos_list'),
    path('ambulance/<uuid:pk>/track/', AmbulanceTrackingView.as_view(), name='ambulance_track'),
    path('', include(router.urls)),
]
