import uuid
from pathlib import Path
from django.db import models


def private_upload_path(instance, filename):
    return f'prescription_uploads/{instance.id}{Path(filename).suffix.lower()}'


class PrescriptionUpload(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Waiting for worker'
        QUEUED = 'QUEUED', 'Queued'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Transcription available'
        FAILED = 'FAILED', 'Processing failed'
        UNAVAILABLE = 'UNAVAILABLE', 'Recognition service unavailable'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.PROTECT, related_name='prescription_uploads')
    file = models.FileField(upload_to=private_upload_path)
    original_filename = models.CharField(max_length=200)
    mime_type = models.CharField(max_length=50)
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    recognition_mode = models.CharField(max_length=15, choices=[('printed', 'Printed'), ('handwritten', 'Handwritten')])
    external_consent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    result = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    error_message = models.CharField(max_length=300, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    lease_until = models.DateTimeField(null=True, blank=True)
    run_token = models.UUIDField(null=True, blank=True)
    review_requested_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['patient', '-created_at'], name='rx_patient_created_idx')]


class PersonalCorrection(models.Model):
    upload = models.ForeignKey(PrescriptionUpload, on_delete=models.PROTECT, related_name='corrections')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class ClinicianReview(models.Model):
    upload = models.ForeignKey(PrescriptionUpload, on_delete=models.PROTECT, related_name='reviews')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.PROTECT)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
