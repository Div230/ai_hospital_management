from django.db import models
from core.models import BaseModel


class Laboratory(BaseModel):
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='lab_profile',
        limit_choices_to={'role': 'laboratory'},
    )
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class LabTestRequest(BaseModel):
    """Created when a doctor orders a test, or a patient books one directly."""
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'), ('SAMPLE_COLLECTED', 'Sample Collected'),
        ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'),
    )
    TEST_TYPE_CHOICES = (
        ('BLOOD', 'Blood Test'), ('XRAY', 'X-Ray'), ('MRI', 'MRI'), ('CT', 'CT Scan'), ('OTHER', 'Other'),
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='lab_test_requests')
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE, related_name='test_requests')
    ordered_by_doctor = models.ForeignKey(
        'doctors.Doctor', on_delete=models.SET_NULL, null=True, blank=True, related_name='ordered_lab_tests',
    )
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    test_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    scheduled_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.test_name} - {self.patient}'


class LabReport(BaseModel):
    """Digital report uploaded by the lab against a test request."""
    test_request = models.OneToOneField(LabTestRequest, on_delete=models.CASCADE, related_name='report')
    file = models.FileField(upload_to='lab_reports/%Y/%m/')
    result_summary = models.TextField(blank=True)
    structured_results = models.JSONField(default=dict, blank=True, help_text='parameter: {value, unit, range, flag}')
    ai_abnormal_findings = models.JSONField(default=list, blank=True)
    reviewed_by = models.CharField(max_length=150, blank=True)
    is_notified = models.BooleanField(default=False)

    def __str__(self):
        return f'Report for {self.test_request}'
