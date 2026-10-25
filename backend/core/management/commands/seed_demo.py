"""Idempotent development fixtures. Every account/document is synthetic."""
from datetime import date, time, timedelta
from decimal import Decimal
from decouple import config
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from accounts.models import User
from patients.models import Patient, MedicalHistory
from doctors.models import Doctor, DoctorAvailability
from hospital_admin.models import Hospital, Department
from laboratory.models import Laboratory, LabTestRequest, LabReport
from pharmacy.models import Pharmacy, Medicine
from appointments.models import Appointment, Prescription, PrescriptionItem
from notifications.models import Notification
import pymupdf


class Command(BaseCommand):
    help = 'Create synthetic development accounts; requires DEBUG and AIHMS_ENABLE_DEMO.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-passwords', action='store_true', help='Reset only the synthetic fixture accounts to AIHMS_DEMO_PASSWORD.')

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG or not config('AIHMS_ENABLE_DEMO', default=False, cast=bool):
            raise CommandError('Synthetic seeding is allowed only in explicitly enabled development environments.')
        password = config('AIHMS_DEMO_PASSWORD', default='')
        if len(password) < 12:
            raise CommandError('Set AIHMS_DEMO_PASSWORD to at least 12 characters, or run scripts/init_env.py.')
        validate_password(password)
        roles = [('admin', 'hospital_admin'), ('doctor', 'doctor'), ('doctor2', 'doctor'),
                 ('patient', 'patient'), ('patient2', 'patient'), ('lab', 'laboratory'), ('pharmacy', 'pharmacy')]
        users = {}
        for name, role in roles:
            user, created = User.objects.get_or_create(email=f'{name}@demo.example.test', defaults={
                'username': f'synthetic_{name}', 'first_name': 'Synthetic', 'last_name': name.title(),
                'role': role, 'is_staff': name == 'admin', 'is_superuser': name == 'admin',
                'is_email_verified': True, 'whatsapp_opt_in': False,
            })
            if user.role != role or not user.username.startswith('synthetic_'):
                raise CommandError('Fixture account collides with an existing non-fixture account.')
            if created or options['reset_passwords']:
                user.set_password(password)
                user.save(update_fields=['password'])
            users[name] = user
        hospital, _ = Hospital.objects.get_or_create(admin=users['admin'], defaults={
            'name': 'AIHMS Synthetic Hospital', 'address': 'Development fixture — not a real hospital',
            'city': 'Synthetic City', 'state': 'Synthetic State', 'pincode': '000000',
            'contact_phone': '', 'contact_email': 'admin@demo.example.test',
        })
        doctors = []
        for index, speciality in enumerate(('General Medicine', 'Dermatology')):
            department, _ = Department.objects.get_or_create(hospital=hospital, name=speciality)
            doctor, _ = Doctor.objects.get_or_create(user=users['doctor' if index == 0 else 'doctor2'], defaults={
                'hospital': hospital, 'department': department, 'specialization': speciality,
                'qualification': 'Synthetic qualification', 'registration_number': f'SYNTHETIC-DOCTOR-{index}',
                'consultation_fee': Decimal('500'), 'is_verified': True,
            })
            doctors.append(doctor)
            for weekday in range(7):
                DoctorAvailability.objects.get_or_create(doctor=doctor, weekday=weekday, start_time=time(9), defaults={
                    'end_time': time(17), 'slot_duration_minutes': 30, 'is_active': True,
                })
        patients = []
        for key in ('patient', 'patient2'):
            patient, _ = Patient.objects.get_or_create(user=users[key], defaults={'date_of_birth': date(1990, 1, 1)})
            patients.append(patient)
            MedicalHistory.objects.get_or_create(patient=patient, title='Synthetic patient-entered history', defaults={
                'entry_type': 'OTHER', 'description': 'Development demonstration only. No real medical history.',
                'date_occurred': date(2026, 1, 1), 'recorded_by': users[key],
            })
        lab, _ = Laboratory.objects.get_or_create(user=users['lab'], defaults={'name': 'Synthetic Laboratory', 'is_verified': True})
        pharmacy, _ = Pharmacy.objects.get_or_create(user=users['pharmacy'], defaults={'name': 'Synthetic Pharmacy', 'is_verified': True})
        Medicine.objects.get_or_create(pharmacy=pharmacy, name='Synthetic demonstration item — not for use', defaults={
            'price': Decimal('10'), 'stock_quantity': 100, 'requires_prescription': True,
        })
        appointment, _ = Appointment.objects.get_or_create(patient=patients[0], doctor=doctors[0], reason='SYNTHETIC completed consultation', defaults={
            'hospital': hospital, 'scheduled_date': date(2026, 1, 1), 'scheduled_time': time(10), 'status': 'COMPLETED', 'duration_minutes': 30,
        })
        prescription, _ = Prescription.objects.get_or_create(appointment=appointment, doctor=doctors[0], patient=patients[0], defaults={
            'diagnosis': 'Synthetic demonstration only — no clinical diagnosis',
        })
        PrescriptionItem.objects.get_or_create(prescription=prescription, medicine_name='Synthetic medication — not for use', defaults={
            'dosage': 'Synthetic dose', 'frequency': 'Synthetic frequency', 'duration_days': 1,
            'instructions': 'This is a software fixture. Do not take medication based on this record.',
        })
        order, _ = LabTestRequest.objects.get_or_create(patient=patients[0], laboratory=lab, test_name='SYNTHETIC demonstration test', defaults={
            'test_type': 'OTHER', 'ordered_by_doctor': doctors[0], 'status': 'COMPLETED',
        })
        if not LabReport.objects.filter(test_request=order).exists():
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((50, 70), 'SYNTHETIC LAB REPORT — SOFTWARE DEMONSTRATION ONLY', fontsize=12)
            page.insert_text((50, 100), 'No real patient information or clinical measurements.', fontsize=11)
            pdf = doc.tobytes()
            doc.close()
            report = LabReport(test_request=order, result_summary='Synthetic report. No clinical values.', is_notified=True)
            report.file.save('synthetic-lab-report.pdf', ContentFile(pdf), save=True)
        Notification.objects.get_or_create(user=users['patient'], title='Welcome to the synthetic AIHMS environment', defaults={
            'channel': 'EMAIL', 'notification_type': 'GENERAL', 'message': 'All seeded people and clinical records are synthetic.',
        })
        self.stdout.write(self.style.SUCCESS('Synthetic fixtures ready. Password: AIHMS_DEMO_PASSWORD in the ignored .env.'))
        for name, _ in roles:
            self.stdout.write(f'{name}: {name}@demo.example.test')
