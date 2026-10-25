from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, time
from threading import Barrier
from unittest import skipUnless
from django.db import connection, close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor, DoctorAvailability
from .models import Appointment


class BookingRegressionTests(TransactionTestCase):
    def setUp(self):
        self.day = timezone.localdate() + timedelta(days=1)
        self.doctor_user = User.objects.create_user(username='doc', email='doc@synthetic.example.test', role='doctor')
        self.doctor = Doctor.objects.create(user=self.doctor_user, specialization='Synthetic', qualification='Synthetic', registration_number='SYNTHETIC-BOOKING', is_verified=True)
        DoctorAvailability.objects.create(doctor=self.doctor, weekday=self.day.weekday(), start_time=time(9), end_time=time(11), slot_duration_minutes=30)
        self.users = [User.objects.create_user(username=f'p{i}', email=f'p{i}@synthetic.example.test', role='patient') for i in range(2)]
        self.clients = []
        for user in self.users:
            Patient.objects.create(user=user)
            client = APIClient()
            client.force_authenticate(user)
            self.clients.append(client)
        self.payload = {'doctor_id': str(self.doctor.pk), 'scheduled_date': str(self.day), 'scheduled_time': '09:00:00'}

    def test_conflict_cancel_and_rebook(self):
        response = self.clients[0].post('/api/appointments/book/', self.payload)
        self.assertEqual(response.status_code, 201, response.data)
        pk = response.data['data']['id']
        self.assertEqual(self.clients[1].post('/api/appointments/book/', self.payload).status_code, 409)
        self.assertEqual(self.clients[1].post(f'/api/appointments/{pk}/cancel/').status_code, 404)
        self.assertEqual(self.clients[0].post(f'/api/appointments/{pk}/cancel/').status_code, 200)
        self.assertEqual(self.clients[1].post('/api/appointments/book/', self.payload).status_code, 201)

    def test_failed_reschedule_preserves_original(self):
        first = self.clients[0].post('/api/appointments/book/', self.payload).data['data']['id']
        self.clients[1].post('/api/appointments/book/', {**self.payload, 'scheduled_time': '09:30:00'})
        response = self.clients[0].post(f'/api/appointments/{first}/reschedule/', {'scheduled_date': str(self.day), 'scheduled_time': '09:30:00'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Appointment.objects.get(pk=first).status, 'CONFIRMED')

    def test_unconfigured_time_rejected(self):
        self.assertEqual(self.clients[0].post('/api/appointments/book/', {**self.payload, 'scheduled_time': '03:15:00'}).status_code, 400)

    @skipUnless(connection.vendor == 'postgresql', 'Concurrency must run against PostgreSQL')
    def test_simultaneous_bookings_reserve_once(self):
        barrier = Barrier(2)
        def reserve(index):
            close_old_connections()
            client = APIClient()
            client.force_authenticate(self.users[index])
            barrier.wait(timeout=10)
            try:
                return client.post('/api/appointments/book/', self.payload).status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(reserve, range(2)))
        self.assertEqual(sorted(statuses), [201, 409])
        self.assertEqual(Appointment.objects.filter(status='CONFIRMED').count(), 1)
