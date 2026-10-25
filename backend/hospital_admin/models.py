from django.db import models
from core.models import BaseModel


class Hospital(BaseModel):
    name = models.CharField(max_length=200)
    admin = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='hospital',
        limit_choices_to={'role': 'hospital_admin'},
    )
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField()
    registration_number = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='hospital_logos/', null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['city'])]

    def __str__(self):
        return self.name


class Department(BaseModel):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(
        'doctors.Doctor', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='headed_departments',
    )

    class Meta:
        unique_together = ('hospital', 'name')

    def __str__(self):
        return f'{self.name} - {self.hospital.name}'


class Staff(BaseModel):
    """Non-doctor hospital staff: nurses, receptionists, technicians etc."""
    ROLE_CHOICES = (
        ('NURSE', 'Nurse'),
        ('RECEPTIONIST', 'Receptionist'),
        ('TECHNICIAN', 'Technician'),
        ('SUPPORT', 'Support Staff'),
    )
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='staff_members')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    joined_on = models.DateField()

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'
