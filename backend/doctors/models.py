from django.db import models
from core.models import BaseModel


class Doctor(BaseModel):
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='doctor_profile',
        limit_choices_to={'role': 'doctor'},
    )
    hospital = models.ForeignKey(
        'hospital_admin.Hospital', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='doctors',
    )
    department = models.ForeignKey(
        'hospital_admin.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='doctors',
    )
    specialization = models.CharField(max_length=150)
    qualification = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, unique=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    is_available_for_video = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    class Meta:
        indexes = [models.Index(fields=['specialization'])]

    def __str__(self):
        return f'Dr. {self.user.get_full_name()} - {self.specialization}'


class DoctorAvailability(BaseModel):
    """Weekly recurring availability slots used by the appointment booking engine."""
    WEEKDAY_CHOICES = (
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
        (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availability_slots')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(default=15)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'weekday', 'start_time')

    def __str__(self):
        return f'{self.doctor} - {self.get_weekday_display()} {self.start_time}-{self.end_time}'


class ClinicalNote(BaseModel):
    """AI-assisted structured clinical note attached to a consultation."""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='clinical_notes')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='clinical_notes')
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='clinical_notes',
    )
    chief_complaint = models.TextField()
    observations = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    ai_generated_summary = models.TextField(blank=True)
    raw_dictation = models.TextField(blank=True, help_text='Free-text notes before AI structuring')

    def __str__(self):
        return f'Note: {self.patient} by {self.doctor} on {self.created_at.date()}'
