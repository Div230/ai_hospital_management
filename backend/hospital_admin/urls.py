from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MyHospitalView, DepartmentViewSet, StaffViewSet, ManagedDoctorsView,
    ManagedPatientsView, AppointmentAnalyticsView, RevenueDashboardView, HospitalStatisticsView,
    UpdateDoctorStatusView, AllDoctorsForAssignmentView,
)

app_name = 'hospital_admin'

router = DefaultRouter()
router.register('departments', DepartmentViewSet, basename='department')
router.register('staff', StaffViewSet, basename='staff')

urlpatterns = [
    path('me/', MyHospitalView.as_view(), name='my_hospital'),
    path('settings/', MyHospitalView.as_view(), name='system_settings'),
    path('doctors/', ManagedDoctorsView.as_view(), name='managed_doctors'),
    path('doctors/all/', AllDoctorsForAssignmentView.as_view(), name='all_doctors'),
    path('doctors/<uuid:pk>/status/', UpdateDoctorStatusView.as_view(), name='update_doctor_status'),
    path('patients/', ManagedPatientsView.as_view(), name='managed_patients'),
    path('analytics/appointments/', AppointmentAnalyticsView.as_view(), name='appointment_analytics'),
    path('analytics/revenue/', RevenueDashboardView.as_view(), name='revenue_dashboard'),
    path('analytics/statistics/', HospitalStatisticsView.as_view(), name='statistics'),
    path('', include(router.urls)),
]
