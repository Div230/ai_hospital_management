from django.urls import path
from .views import HealthView, PatientDashboardView, DoctorDashboardView, LabDashboardView, PharmacyDashboardView

app_name = 'core'

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('dashboard/patient/', PatientDashboardView.as_view(), name='patient_dashboard'),
    path('dashboard/doctor/', DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('dashboard/lab/', LabDashboardView.as_view(), name='lab_dashboard'),
    path('dashboard/pharmacy/', PharmacyDashboardView.as_view(), name='pharmacy_dashboard'),
]
