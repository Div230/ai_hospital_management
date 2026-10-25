import logging
from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from core.permissions import IsPatient
from rest_framework.exceptions import PermissionDenied
from notifications.services import notify_user, dispatch_webhook_event
from .models import (
    Patient, FamilyMember, MedicalHistory, MedicalReport,
    MedicineReminder, VaccinationReminder, SOSAlert, AmbulanceRequest,
)
from .serializers import (
    PatientSerializer, FamilyMemberSerializer, MedicalHistorySerializer,
    MedicalReportSerializer, MedicineReminderSerializer, VaccinationReminderSerializer,
    SOSAlertSerializer, AmbulanceRequestSerializer,
)

logger = logging.getLogger('healthcare')


class MyPatientProfileView(generics.RetrieveUpdateAPIView):
    """Patient's own profile — auto-created on first access if missing."""
    serializer_class = PatientSerializer
    permission_classes = [IsPatient]

    def get_object(self):
        profile, _ = Patient.objects.get_or_create(user=self.request.user)
        return profile


class FamilyMemberViewSet(viewsets.ModelViewSet):
    serializer_class = FamilyMemberSerializer
    permission_classes = [IsPatient]
    filterset_fields = ['relation']
    search_fields = ['full_name']

    def get_queryset(self):
        return FamilyMember.objects.filter(patient__user=self.request.user)

    def perform_create(self, serializer):
        patient, _ = Patient.objects.get_or_create(user=self.request.user)
        serializer.save(patient=patient)


class MedicalHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['entry_type']
    search_fields = ['title']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicalHistory.objects.filter(patient__user=user)
        if user.role == 'doctor':
            # Doctors can view (not create) history of patients they've treated
            return MedicalHistory.objects.filter(patient__appointments__doctor__user=user, patient__appointments__status__in=['CONFIRMED', 'COMPLETED']).distinct()
        return MedicalHistory.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != 'patient':
            raise PermissionDenied()
        patient, _ = Patient.objects.get_or_create(user=self.request.user)
        serializer.save(patient=patient, recorded_by=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.role != 'patient' or serializer.instance.recorded_by_id != self.request.user.pk:
            raise PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role != 'patient' or instance.recorded_by_id != self.request.user.pk:
            raise PermissionDenied()
        instance.soft_delete()


class MedicalReportViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']
    serializer_class = MedicalReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['report_type', 'status']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicalReport.objects.filter(patient__user=user)
        if user.role == 'doctor':
            return MedicalReport.objects.filter(patient__appointments__doctor__user=user, patient__appointments__status__in=['CONFIRMED', 'COMPLETED']).distinct()
        return MedicalReport.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != 'patient':
            raise PermissionDenied()
        patient, _ = Patient.objects.get_or_create(user=self.request.user)
        report = serializer.save(patient=patient, uploaded_by=self.request.user, status='UPLOADED')
        self._queue_analysis(report)

    @staticmethod
    def _queue_analysis(report):
        from ai_assistant.tasks import analyze_medical_report_task
        from django.db import transaction
        def enqueue():
            try:
                analyze_medical_report_task.delay(str(report.id))
            except Exception:
                logger.warning('Report queue unavailable')
                MedicalReport.objects.filter(pk=report.pk).update(status='FAILED')
        transaction.on_commit(enqueue)



class MedicineReminderViewSet(viewsets.ModelViewSet):
    serializer_class = MedicineReminderSerializer
    permission_classes = [IsPatient]
    filterset_fields = ['is_active']

    def get_queryset(self):
        return MedicineReminder.objects.filter(patient__user=self.request.user)

    def perform_create(self, serializer):
        patient, _ = Patient.objects.get_or_create(user=self.request.user)
        serializer.save(patient=patient)


class VaccinationReminderViewSet(viewsets.ModelViewSet):
    serializer_class = VaccinationReminderSerializer
    permission_classes = [IsPatient]
    filterset_fields = ['is_completed']

    def get_queryset(self):
        return VaccinationReminder.objects.filter(patient__user=self.request.user)

    def perform_create(self, serializer):
        patient, _ = Patient.objects.get_or_create(user=self.request.user)
        serializer.save(patient=patient)


class TriggerSOSView(APIView):
    """One-click Emergency SOS. Creates alert, mock-dispatches an ambulance,
    and fires WhatsApp/Email alerts to emergency contacts."""
    permission_classes = [IsPatient]

    def post(self, request):
        return Response({'message': 'Emergency dispatch is not connected. Call your local emergency service directly.'}, status=503)



class MySOSAlertsView(generics.ListAPIView):
    serializer_class = SOSAlertSerializer
    permission_classes = [IsPatient]

    def get_queryset(self):
        return SOSAlert.objects.filter(patient__user=self.request.user)


class AmbulanceTrackingView(APIView):
    """Mock live tracking — returns current (simulated) location + ETA."""
    permission_classes = [IsPatient]

    def get(self, request, pk):
        try:
            ambulance = AmbulanceRequest.objects.get(pk=pk, sos_alert__patient__user=request.user)
        except AmbulanceRequest.DoesNotExist:
            return Response({'success': False, 'message': 'Not found.'}, status=404)
        return Response({'success': True, 'data': AmbulanceRequestSerializer(ambulance).data})
