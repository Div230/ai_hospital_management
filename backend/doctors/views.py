from rest_framework import generics, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from core.permissions import IsDoctor
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from patients.models import Patient, MedicalHistory, MedicalReport
from patients.serializers import MedicalHistorySerializer, MedicalReportSerializer, PatientSerializer
from .models import Doctor, DoctorAvailability, ClinicalNote
from .serializers import (
    DoctorSerializer, DoctorPublicSerializer, DoctorAvailabilitySerializer,
    ClinicalNoteSerializer,
)
from ai_assistant.services.chains import structure_clinical_note


class MyDoctorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [IsDoctor]

    def get_object(self):
        profile, _ = Doctor.objects.get_or_create(
            user=self.request.user,
            defaults={'specialization': '', 'qualification': '',
                      'registration_number': f'UNVERIFIED-{self.request.user.id}'},
        )
        return profile


class DoctorListView(generics.ListAPIView):
    """Public directory for patients to browse/search doctors when booking."""
    queryset = Doctor.objects.filter(is_verified=True, user__is_active=True)
    serializer_class = DoctorPublicSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['specialization', 'hospital', 'is_available_for_video']
    search_fields = ['specialization', 'user__first_name', 'user__last_name']


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return DoctorAvailability.objects.filter(doctor__user=self.request.user)

    def perform_create(self, serializer):
        doctor, _ = Doctor.objects.get_or_create(user=self.request.user)
        serializer.save(doctor=doctor)


class DoctorPatientListView(generics.ListAPIView):
    """Patients this doctor has an appointment history with."""
    permission_classes = [IsDoctor]
    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(appointments__doctor__user=self.request.user, appointments__status__in=['CONFIRMED', 'COMPLETED']).distinct()


class ClinicalNoteViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']
    serializer_class = ClinicalNoteSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return ClinicalNote.objects.filter(doctor__user=self.request.user)

    def perform_create(self, serializer):
        doctor, _ = Doctor.objects.get_or_create(user=self.request.user)
        patient = serializer.validated_data['patient']
        appointment = serializer.validated_data.get('appointment')
        if not patient.appointments.filter(doctor=doctor, status__in=['CONFIRMED', 'COMPLETED']).exists():
            raise PermissionDenied('Patient is outside your clinical workflow.')
        if appointment and (appointment.patient_id != patient.pk or appointment.doctor_id != doctor.pk):
            raise PermissionDenied('Appointment does not match this doctor and patient.')
        raw_dictation = self.request.data.get('raw_dictation', '')
        ai_summary = ''
        structured = {}
        if raw_dictation and self.request.data.get('external_ai_consent') is True:
            structured = structure_clinical_note(raw_dictation)
            ai_summary = structured.get('summary', '')
        serializer.save(
            doctor=doctor,
            ai_generated_summary=ai_summary,
            chief_complaint=serializer.validated_data.get('chief_complaint') or structured.get('chief_complaint', ''),
            observations=serializer.validated_data.get('observations') or structured.get('observations', ''),
            diagnosis=serializer.validated_data.get('diagnosis') or structured.get('diagnosis', ''),
        )


class DoctorSlotsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        from datetime import date
        from rest_framework.exceptions import ValidationError, NotFound
        from appointments.services import available_slots
        try:
            day = date.fromisoformat(request.query_params.get('date', ''))
        except ValueError:
            raise ValidationError({'date': 'Use YYYY-MM-DD.'})
        try:
            doctor = Doctor.objects.get(pk=pk, is_verified=True, user__is_active=True)
        except Doctor.DoesNotExist:
            raise NotFound()
        return Response({'date': day, 'timezone': 'Asia/Kolkata', 'slots': list(available_slots(doctor, day))})
