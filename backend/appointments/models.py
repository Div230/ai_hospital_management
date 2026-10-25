from django.db import models
from core.models import BaseModel


class Appointment(BaseModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'),
        ('RESCHEDULED', 'Rescheduled'), ('NO_SHOW', 'No Show'),
    )
    MODE_CHOICES = (('IN_PERSON', 'In Person'), ('VIDEO', 'Video Consultation'))

    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='appointments')
    hospital = models.ForeignKey(
        'hospital_admin.Hospital', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='appointments',
    )
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=15)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='IN_PERSON')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField(blank=True)
    video_room_id = models.CharField(max_length=100, blank=True)
    cancelled_reason = models.TextField(blank=True)
    rescheduled_from = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rescheduled_to',
    )

    class Meta:
        indexes = [
            models.Index(fields=['doctor', 'scheduled_date']),
            models.Index(fields=['patient', 'status']),
        ]
        ordering = ['-scheduled_date', '-scheduled_time']
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'scheduled_date', 'scheduled_time'],
                condition=models.Q(status__in=['PENDING', 'CONFIRMED'], is_deleted=False), name='unique_active_doctor_slot'),
            models.CheckConstraint(condition=models.Q(duration_minutes__gte=1, duration_minutes__lte=120), name='valid_appointment_duration'),
        ]

    def __str__(self):
        return f'{self.patient} with {self.doctor} on {self.scheduled_date} {self.scheduled_time}'


class Prescription(BaseModel):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    diagnosis = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_sent_to_pharmacy = models.BooleanField(default=False)

    def __str__(self):
        return f'Prescription for {self.patient} by {self.doctor}'


class PrescriptionItem(BaseModel):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField()
    instructions = models.TextField(blank=True)
    ai_explanation = models.TextField(
        blank=True, help_text='AI-generated plain-language explanation of this medicine'
    )

    def __str__(self):
        return f'{self.medicine_name} - {self.prescription}'
