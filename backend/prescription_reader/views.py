import hashlib
from pathlib import Path
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from patients.models import Patient
from core.models import AuditLog
from .models import PrescriptionUpload
from .serializers import UploadInputSerializer, UploadSerializer, CorrectionSerializer, ReviewSerializer
from .tasks import enqueue_dispatch


def audit(request, action_name, upload):
    AuditLog.objects.create(user=request.user, action=action_name, model_name='PrescriptionUpload',
                            object_id=str(upload.pk), path=request.path, method=request.method)


class PrescriptionReaderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UploadSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    filterset_fields = ['status']
    search_fields = ['original_filename']

    def get_queryset(self):
        qs = PrescriptionUpload.objects.select_related('patient__user').prefetch_related('reviews__doctor__user', 'corrections')
        user = self.request.user
        if user.role == 'patient':
            return qs.filter(patient__user=user)
        if user.role == 'doctor':
            return qs.filter(review_requested_at__isnull=False, patient__appointments__doctor__user=user,
                             patient__appointments__status__in=['CONFIRMED', 'COMPLETED']).distinct()
        return qs.none()

    @extend_schema(request=UploadInputSerializer, responses={201: UploadSerializer})
    def create(self, request):
        if request.user.role != 'patient':
            raise PermissionDenied('Only patients can upload their prescriptions.')
        serializer = UploadInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        file = data['file']
        from core.documents import validate_upload
        mime = validate_upload(file)
        digest = hashlib.sha256(file.read()).hexdigest()
        file.seek(0)
        patient, _ = Patient.objects.get_or_create(user=request.user)
        with transaction.atomic():
            upload = PrescriptionUpload.objects.create(patient=patient, file=file, mime_type=mime,
                original_filename=Path(file.name).name[:200], size_bytes=file.size, sha256=digest,
                recognition_mode=data['recognition_mode'], external_consent=data['external_consent'])
            audit(request, 'CREATE', upload)
            transaction.on_commit(enqueue_dispatch)
        return Response(self.get_serializer(upload).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        upload = self.get_object()
        audit(request, 'VIEW', upload)
        return Response(self.get_serializer(upload).data)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        with transaction.atomic():
            upload = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            if request.user.role != 'patient':
                raise PermissionDenied()
            if upload.status not in ('FAILED', 'UNAVAILABLE'):
                raise ValidationError('Only failed or unavailable processing can be retried.')
            upload.status, upload.attempt_count, upload.lease_until = 'PENDING', 0, None
            upload.error_code = upload.error_message = ''
            upload.save(update_fields=['status', 'attempt_count', 'lease_until', 'error_code', 'error_message', 'updated_at'])
            audit(request, 'UPDATE', upload)
            transaction.on_commit(enqueue_dispatch)
        return Response(self.get_serializer(upload).data)

    @action(detail=True, methods=['post'])
    @extend_schema(request=CorrectionSerializer, responses={201: CorrectionSerializer})
    def correction(self, request, pk=None):
        upload = self.get_object()
        if request.user.role != 'patient' or upload.status != 'COMPLETED':
            raise PermissionDenied('Personal corrections are available for your completed transcriptions.')
        serializer = CorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(upload=upload)
        audit(request, 'UPDATE', upload)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'], url_path='request-review')
    def request_review(self, request, pk=None):
        upload = self.get_object()
        if request.user.role != 'patient':
            raise PermissionDenied()
        upload.review_requested_at = timezone.now()
        upload.save(update_fields=['review_requested_at', 'updated_at'])
        audit(request, 'UPDATE', upload)
        return Response(self.get_serializer(upload).data)

    @action(detail=True, methods=['post'])
    @extend_schema(request=ReviewSerializer, responses={201: ReviewSerializer})
    def review(self, request, pk=None):
        upload = self.get_object()
        if request.user.role != 'doctor':
            raise PermissionDenied('Only a treating doctor can record a clinical review.')
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(upload=upload, doctor=request.user.doctor_profile)
        audit(request, 'UPDATE', upload)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        upload = self.get_object()
        if upload.status != 'COMPLETED':
            raise ValidationError('Transcription is not available yet.')
        text = upload.result.get('transcription', '')
        notice = upload.result.get('notice', '')
        response = HttpResponse(text + '\n\n' + notice, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="prescription-transcription.txt"'
        response['Cache-Control'] = 'private, no-store'
        audit(request, 'VIEW', upload)
        return response
