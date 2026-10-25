"""Database outbox plus expiring leases makes enqueue/worker failure recoverable."""
import hashlib
import logging
import uuid
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import PrescriptionUpload

logger = logging.getLogger('healthcare')


def enqueue_dispatch():
    try:
        dispatch_pending.delay()
    except Exception:
        # Durable PENDING rows are recovered by beat after broker restoration.
        logger.warning('Prescription queue unavailable; pending uploads retained')


@shared_task(name='prescription_reader.tasks.dispatch_pending')
def dispatch_pending():
    now = timezone.now()
    ids = list(PrescriptionUpload.objects.filter(
        Q(status='PENDING') | Q(status__in=['QUEUED', 'PROCESSING'], lease_until__lt=now)
    ).values_list('pk', flat=True)[:50])
    for pk in ids:
        with transaction.atomic():
            upload = PrescriptionUpload.objects.select_for_update().get(pk=pk)
            if upload.status not in ('PENDING', 'QUEUED', 'PROCESSING'):
                continue
            if upload.status != 'PENDING' and upload.lease_until and upload.lease_until > now:
                continue
            if upload.attempt_count >= 3:
                upload.status = 'FAILED'
                upload.error_code = 'retry_limit'
                upload.error_message = 'Processing stopped after three attempts. The original is preserved.'
                upload.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])
                continue
            upload.status = 'QUEUED'
            upload.run_token = None
            upload.lease_until = now + timedelta(minutes=5)
            upload.save(update_fields=['status', 'run_token', 'lease_until', 'updated_at'])
        try:
            process_upload.delay(str(pk))
        except Exception:
            PrescriptionUpload.objects.filter(pk=pk, status='QUEUED').update(status='PENDING', lease_until=None)
            logger.warning('Prescription enqueue deferred')


@shared_task(acks_late=True, reject_on_worker_lost=True, soft_time_limit=210, time_limit=240)
def process_upload(upload_id):
    from .providers import process_document, ProviderUnavailable
    from ai_assistant.services.ocr import OCRUnavailable
    from notifications.models import Notification
    with transaction.atomic():
        upload = PrescriptionUpload.objects.select_for_update().filter(pk=upload_id).first()
        if not upload or upload.status not in ('PENDING', 'QUEUED', 'PROCESSING'):
            return
        if upload.status == 'PROCESSING' and upload.lease_until and upload.lease_until > timezone.now():
            return
        if upload.attempt_count >= 3:
            PrescriptionUpload.objects.filter(pk=upload_id).update(status='FAILED', error_code='retry_limit')
            return
        token = uuid.uuid4()
        upload.run_token = token
        upload.status = 'PROCESSING'
        upload.attempt_count += 1
        upload.lease_until = timezone.now() + timedelta(minutes=5)
        upload.save(update_fields=['run_token', 'status', 'attempt_count', 'lease_until', 'updated_at'])
    try:
        with upload.file.open('rb') as original:
            data = original.read(settings.MAX_UPLOAD_BYTES + 1)
        if hashlib.sha256(data).hexdigest() != upload.sha256:
            raise ValueError('Stored file integrity check failed.')
        result = process_document(data, upload.original_filename, upload.recognition_mode, vision_config={
            'base_url': settings.VISION_BASE_URL, 'model': settings.VISION_MODEL,
            'api_key': settings.VISION_API_KEY, 'is_external': settings.VISION_IS_EXTERNAL,
            'external_enabled': settings.EXTERNAL_AI_ENABLED, 'consent': upload.external_consent,
        })
    except (ProviderUnavailable, OCRUnavailable) as exc:
        PrescriptionUpload.objects.filter(pk=upload_id, run_token=token, status='PROCESSING').update(
            status='UNAVAILABLE', error_code='provider_unavailable', error_message=str(exc)[:300], lease_until=None,
            updated_at=timezone.now())
        return
    except Exception:
        # Provider exceptions may contain request bodies or secrets. Do not log them.
        logger.warning('Prescription processing failed')
        PrescriptionUpload.objects.filter(pk=upload_id, run_token=token, status='PROCESSING').update(
            status='FAILED', error_code='processing_failed',
            error_message='The document could not be processed. Retry or ask a clinician to read the original.',
            lease_until=None, updated_at=timezone.now())
        return
    with transaction.atomic():
        updated = PrescriptionUpload.objects.filter(pk=upload_id, run_token=token, status='PROCESSING').update(
            status='COMPLETED', result=result, error_code='', error_message='', lease_until=None, updated_at=timezone.now())
        if updated:
            Notification.objects.create(user_id=upload.patient.user_id, channel='EMAIL', notification_type='GENERAL',
                                        title='Prescription transcription ready',
                                        message='A prescription transcription is available in your portal. Review uncertainty before use.')
