from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsPatient, IsDoctor, IsHospitalAdmin, IsLaboratory, IsPharmacy


class PatientDashboardView(APIView):
    permission_classes = [IsPatient]

    def get(self, request):
        from patients.models import Patient
        from appointments.models import Appointment
        patient, _ = Patient.objects.get_or_create(user=request.user)
        upcoming = Appointment.objects.filter(
            patient=patient, status='CONFIRMED', scheduled_date__gte=timezone.now().date()
        ).order_by('scheduled_date')[:5]

        return Response({
            'success': True,
            'ai_health_score': patient.ai_health_score,
            'ai_risk_flags': patient.ai_risk_flags,
            'upcoming_appointments': [
                {'id': a.id, 'doctor': a.doctor.user.get_full_name(),
                 'date': a.scheduled_date, 'time': a.scheduled_time, 'mode': a.mode}
                for a in upcoming
            ],
            'active_medicine_reminders': patient.medicine_reminders.filter(is_active=True).count(),
            'pending_vaccinations': patient.vaccination_reminders.filter(is_completed=False).count(),
            'unread_notifications': request.user.notifications.filter(is_read=False).count(),
        })


class DoctorDashboardView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        from doctors.models import Doctor
        from appointments.models import Appointment
        doctor, _ = Doctor.objects.get_or_create(
            user=request.user,
            defaults={'specialization': '', 'qualification': '',
                      'registration_number': f'UNVERIFIED-{request.user.id}'},
        )
        today_appointments = Appointment.objects.filter(doctor=doctor, scheduled_date=timezone.now().date())

        return Response({
            'success': True,
            'todays_appointments': today_appointments.count(),
            'pending_appointments': Appointment.objects.filter(doctor=doctor, status='PENDING').count(),
            'total_patients': Appointment.objects.filter(doctor=doctor).values('patient').distinct().count(),
            'rating': str(doctor.rating),
            'schedule_today': [
                {'id': a.id, 'patient': a.patient.user.get_full_name(), 'time': a.scheduled_time,
                 'mode': a.mode, 'status': a.status}
                for a in today_appointments.order_by('scheduled_time')
            ],
        })


class LabDashboardView(APIView):
    permission_classes = [IsLaboratory]

    def get(self, request):
        from laboratory.models import Laboratory, LabTestRequest
        lab, _ = Laboratory.objects.get_or_create(
            user=request.user, defaults={'name': request.user.get_full_name() or 'Lab'}
        )
        return Response({
            'success': True,
            'pending_requests': LabTestRequest.objects.filter(laboratory=lab, status='REQUESTED').count(),
            'in_progress': LabTestRequest.objects.filter(laboratory=lab, status='IN_PROGRESS').count(),
            'completed_today': LabTestRequest.objects.filter(
                laboratory=lab, status='COMPLETED', updated_at__date=timezone.now().date()
            ).count(),
        })


class PharmacyDashboardView(APIView):
    permission_classes = [IsPharmacy]

    def get(self, request):
        from pharmacy.models import Pharmacy, Medicine, MedicineOrder
        pharmacy, _ = Pharmacy.objects.get_or_create(
            user=request.user, defaults={'name': request.user.get_full_name() or 'Pharmacy'}
        )
        return Response({
            'success': True,
            'pending_orders': MedicineOrder.objects.filter(pharmacy=pharmacy, status='PLACED').count(),
            'low_stock_medicines': Medicine.objects.filter(pharmacy=pharmacy, stock_quantity__lt=10).count(),
            'total_medicines': Medicine.objects.filter(pharmacy=pharmacy).count(),
            'orders_today': MedicineOrder.objects.filter(
                pharmacy=pharmacy, created_at__date=timezone.now().date()
            ).count(),
        })


class HealthView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from django.db import connection
        from django.core.cache import cache
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            cache.set('aihms:health', True, 10)
            if cache.get('aihms:health') is not True:
                raise RuntimeError()
        except Exception:
            return Response({'status': 'unavailable'}, status=503)
        return Response({'status': 'ok'})
