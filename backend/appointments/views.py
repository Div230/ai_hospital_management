import logging
from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from core.permissions import IsPatient, IsDoctor
from django.db import transaction, IntegrityError
from rest_framework.exceptions import PermissionDenied, ValidationError
from . import services
from notifications.services import notify_user, dispatch_webhook_event
from doctors.models import Doctor
from patients.models import Patient
from .models import Appointment, Prescription, PrescriptionItem
from .serializers import (
    AppointmentSerializer, AppointmentBookSerializer, AppointmentRescheduleSerializer,
    PrescriptionSerializer,
)

logger = logging.getLogger('healthcare')


class BookAppointmentView(APIView):
    permission_classes = [IsPatient]

    def post(self, request):
        serializer = AppointmentBookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient, _ = Patient.objects.get_or_create(user=request.user)
        try:
            appointment = services.book(patient, data)
        except IntegrityError:
            raise services.SlotConflict()
        doctor = appointment.doctor
        notify_user(
            request.user, 'APPOINTMENT_CONFIRMED', 'Appointment Confirmed',
            f'Your appointment with Dr. {doctor.user.get_full_name()} on '
            f'{appointment.scheduled_date} at {appointment.scheduled_time} is confirmed.',
            channel='WHATSAPP',
        )
        notify_user(
            doctor.user, 'APPOINTMENT_CONFIRMED', 'New Appointment Booked',
            f'{patient.user.get_full_name()} booked an appointment on '
            f'{appointment.scheduled_date} at {appointment.scheduled_time}.',
            channel='EMAIL',
        )
        dispatch_webhook_event(
            doctor.hospital.admin if doctor.hospital else None,
            'APPOINTMENT_BOOKED',
            {
                'appointment_id': str(appointment.id),
                'patient': patient.user.get_full_name(),
                'doctor': doctor.user.get_full_name(),
                'scheduled_date': str(appointment.scheduled_date),
                'scheduled_time': str(appointment.scheduled_time),
                'mode': appointment.mode,
            },
        )
        return Response(
            {'success': True, 'data': AppointmentSerializer(appointment).data},
            status=status.HTTP_201_CREATED,
        )


class MyAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'mode']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Appointment.objects.filter(patient__user=user)
        if user.role == 'doctor':
            return Appointment.objects.filter(doctor__user=user)
        return Appointment.objects.none()


class CancelAppointmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        appointment = services.cancel(request.user, pk, request.data.get('reason', ''))

        notify_user(
            appointment.patient.user, 'APPOINTMENT_CANCELLED', 'Appointment Cancelled',
            f'Your appointment on {appointment.scheduled_date} has been cancelled.',
            channel='EMAIL',
        )
        dispatch_webhook_event(
            appointment.hospital.admin if appointment.hospital else None,
            'APPOINTMENT_CANCELLED',
            {
                'appointment_id': str(appointment.id),
                'patient': appointment.patient.user.get_full_name(),
                'doctor': appointment.doctor.user.get_full_name(),
                'cancelled_reason': appointment.cancelled_reason,
            },
        )
        return Response({'success': True, 'data': AppointmentSerializer(appointment).data})

    @staticmethod
    def _get_appointment(request, pk):
        user = request.user
        qs = Appointment.objects.filter(pk=pk)
        if user.role == 'patient':
            return qs.filter(patient__user=user).first()
        if user.role == 'doctor':
            return qs.filter(doctor__user=user).first()
        return None


class RescheduleAppointmentView(APIView):
    permission_classes = [IsPatient]

    def post(self, request, pk):
        serializer = AppointmentRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            new_appointment = services.reschedule(request.user, pk, serializer.validated_data)
        except IntegrityError:
            raise services.SlotConflict()
        notify_user(
            request.user, 'APPOINTMENT_CONFIRMED', 'Appointment Rescheduled',
            f'Your appointment has been moved to {new_appointment.scheduled_date} '
            f'at {new_appointment.scheduled_time}.',
            channel='WHATSAPP',
        )
        return Response({'success': True, 'data': AppointmentSerializer(new_appointment).data})


class PrescriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PrescriptionSerializer
    http_method_names = ['get', 'post', 'head', 'options']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            return Prescription.objects.filter(doctor__user=user)
        if user.role == 'patient':
            return Prescription.objects.filter(patient__user=user)
        if user.role == 'pharmacy':
            return Prescription.objects.filter(orders__pharmacy__user=user).distinct()
        return Prescription.objects.none()

    def perform_create(self, serializer):
        from doctors.models import Doctor
        from ai_assistant.services.chains import explain_medicine

        if self.request.user.role != 'doctor':
            raise PermissionDenied('Only doctors can issue prescriptions.')
        doctor = Doctor.objects.get(user=self.request.user)
        appointment = serializer.validated_data['appointment']
        if appointment.doctor_id != doctor.pk or appointment.status not in ('CONFIRMED', 'COMPLETED'):
            raise PermissionDenied('This appointment is outside your clinical workflow.')
        with transaction.atomic():
            prescription = serializer.save(doctor=doctor, patient=appointment.patient)
        notify_user(
            prescription.patient.user, 'PRESCRIPTION_UPDATE', 'New Prescription Issued',
            f'Dr. {doctor.user.get_full_name()} has issued a new prescription for you.',
            channel='WHATSAPP',
        )
        dispatch_webhook_event(
            prescription.appointment.hospital.admin if prescription.appointment and prescription.appointment.hospital else None,
            'PRESCRIPTION_ISSUED',
            {
                'prescription_id': str(prescription.id),
                'patient': prescription.patient.user.get_full_name(),
                'doctor': doctor.user.get_full_name(),
                'diagnosis': prescription.diagnosis,
            },
        )
