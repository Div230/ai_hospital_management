from django.db import models
from core.models import BaseModel


class Patient(BaseModel):
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    )
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'), ('O', 'Other'))

    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='patient_profile',
        limit_choices_to={'role': 'patient'},
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    address = models.TextField(blank=True)
    allergies = models.TextField(blank=True, help_text='Comma-separated known allergies')
    chronic_conditions = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)

    # AI-derived, recomputed periodically by the AI health score service
    ai_health_score = models.PositiveIntegerField(null=True, blank=True, help_text='0-100')
    ai_risk_flags = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.user.email})'


class FamilyMember(BaseModel):
    """Linked family health records managed under one patient account."""
    RELATION_CHOICES = (
        ('SPOUSE', 'Spouse'), ('CHILD', 'Child'), ('PARENT', 'Parent'),
        ('SIBLING', 'Sibling'), ('OTHER', 'Other'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='family_members')
    full_name = models.CharField(max_length=150)
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Patient.GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=3, choices=Patient.BLOOD_GROUP_CHOICES, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.full_name} ({self.get_relation_display()}) of {self.patient}'


class MedicalHistory(BaseModel):
    """A single medical event/entry in the patient's EHR timeline."""
    ENTRY_TYPE_CHOICES = (
        ('DIAGNOSIS', 'Diagnosis'), ('SURGERY', 'Surgery'), ('ILLNESS', 'Illness'),
        ('VACCINATION', 'Vaccination'), ('ALLERGY', 'Allergy'), ('OTHER', 'Other'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_occurred = models.DateField()
    recorded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recorded_history_entries',
    )

    class Meta:
        ordering = ['-date_occurred']
        indexes = [models.Index(fields=['patient', 'entry_type'])]

    def __str__(self):
        return f'{self.title} - {self.patient}'


class MedicalReport(BaseModel):
    """Patient-uploaded report (PDF/Image) — feeds the OCR + AI analyzer pipeline."""
    REPORT_TYPE_CHOICES = (
        ('BLOOD', 'Blood Test'), ('XRAY', 'X-Ray'), ('MRI', 'MRI'),
        ('CT', 'CT Scan'), ('PRESCRIPTION', 'Prescription'), ('OTHER', 'Other'),
    )
    STATUS_CHOICES = (
        ('UPLOADED', 'Uploaded'), ('PROCESSING', 'Processing'),
        ('ANALYZED', 'Analyzed'), ('FAILED', 'Failed'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_reports')
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='+')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    file = models.FileField(upload_to='medical_reports/%Y/%m/')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='UPLOADED')

    ocr_extracted_text = models.TextField(blank=True)
    ai_structured_summary = models.JSONField(default=dict, blank=True)
    ai_abnormal_values = models.JSONField(default=list, blank=True)

    class Meta:
        indexes = [models.Index(fields=['patient', 'report_type'])]

    def __str__(self):
        return f'{self.get_report_type_display()} - {self.patient}'


class MedicineReminder(BaseModel):
    FREQUENCY_CHOICES = (
        ('ONCE_DAILY', 'Once Daily'), ('TWICE_DAILY', 'Twice Daily'),
        ('THRICE_DAILY', 'Thrice Daily'), ('WEEKLY', 'Weekly'), ('CUSTOM', 'Custom'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medicine_reminders')
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    reminder_times = models.JSONField(default=list, help_text='List of HH:MM strings')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.medicine_name} - {self.patient}'


class VaccinationReminder(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vaccination_reminders')
    vaccine_name = models.CharField(max_length=200)
    scheduled_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.vaccine_name} - {self.patient}'


class SOSAlert(BaseModel):
    STATUS_CHOICES = (
        ('TRIGGERED', 'Triggered'), ('AMBULANCE_DISPATCHED', 'Ambulance Dispatched'),
        ('RESOLVED', 'Resolved'), ('CANCELLED', 'Cancelled'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sos_alerts')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='TRIGGERED')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'SOS by {self.patient} at {self.created_at}'


class AmbulanceRequest(BaseModel):
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'), ('EN_ROUTE', 'En Route'),
        ('ARRIVED', 'Arrived'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'),
    )
    sos_alert = models.ForeignKey(SOSAlert, on_delete=models.CASCADE, related_name='ambulance_requests')
    driver_name = models.CharField(max_length=150, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='REQUESTED')
    # Mock live tracking — in production this would stream via WebSocket/Channels
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    eta_minutes = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f'Ambulance for {self.sos_alert}'
