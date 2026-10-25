import logging
from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from core.permissions import IsLaboratory, IsPatient
from .models import Laboratory, LabTestRequest, LabReport
from .serializers import LaboratorySerializer, LabTestRequestSerializer, LabReportSerializer

logger = logging.getLogger('healthcare')


class MyLabProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = LaboratorySerializer
    permission_classes = [IsLaboratory]

    def get_object(self):
        profile, _ = Laboratory.objects.get_or_create(
            user=self.request.user, defaults={'name': self.request.user.get_full_name() or 'Lab'}
        )
        return profile


class LabTestRequestViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']
    serializer_class = LabTestRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'test_type']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'laboratory':
            return LabTestRequest.objects.filter(laboratory__user=user)
        if user.role == 'patient':
            return LabTestRequest.objects.filter(patient__user=user)
        if user.role == 'doctor':
            return LabTestRequest.objects.filter(ordered_by_doctor__user=user)
        return LabTestRequest.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role == 'patient':
            from patients.models import Patient
            patient, _ = Patient.objects.get_or_create(user=self.request.user)
            serializer.save(patient=patient)
        elif self.request.user.role == 'doctor':
            from doctors.models import Doctor
            doctor, _ = Doctor.objects.get_or_create(user=self.request.user)
            serializer.save(ordered_by_doctor=doctor)
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()


class UploadLabReportView(APIView):
    """
    Lab uploads the digital report (Blood/X-Ray/MRI/CT). Runs OCR + AI
    abnormal-value detection, then auto-notifies the patient.
    """
    permission_classes = [IsLaboratory]

    def post(self, request, test_request_id):
        try:
            test_request = LabTestRequest.objects.get(id=test_request_id, laboratory__user=request.user)
        except LabTestRequest.DoesNotExist:
            return Response({'success': False, 'message': 'Test request not found.'}, status=404)

        serializer = LabReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(test_request=test_request)

        # Queue OCR + AI analysis + patient notification on Celery so this
        # request returns immediately. Falls back to running inline if no
        # Celery worker is reachable (e.g. Redis isn't running).
        from ai_assistant.tasks import analyze_lab_report_task
        try:
            analyze_lab_report_task.delay(str(report.id))
        except Exception as e:
            logger.warning(f'Celery unavailable ({e}), running lab report analysis synchronously instead.')
            analyze_lab_report_task(str(report.id))
            report.refresh_from_db()

        return Response(
            {'success': True, 'data': LabReportSerializer(report).data,
             'message': 'Report uploaded — AI analysis is processing and the patient will be notified once complete.'},
            status=status.HTTP_201_CREATED,
        )

class LaboratoryListView(generics.ListAPIView):
    """Public directory of verified labs — patients/doctors browse this to pick a lab when booking a test."""
    queryset = Laboratory.objects.filter(is_verified=True)
    serializer_class = LaboratorySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'city']
