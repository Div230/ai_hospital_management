from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BookAppointmentView, MyAppointmentsView, CancelAppointmentView,
    RescheduleAppointmentView, PrescriptionViewSet,
)

app_name = 'appointments'

router = DefaultRouter()
router.register('prescriptions', PrescriptionViewSet, basename='prescription')

urlpatterns = [
    path('book/', BookAppointmentView.as_view(), name='book'),
    path('my/', MyAppointmentsView.as_view(), name='my_appointments'),
    path('<uuid:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel'),
    path('<uuid:pk>/reschedule/', RescheduleAppointmentView.as_view(), name='reschedule'),
    path('', include(router.urls)),
]
