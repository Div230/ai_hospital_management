"""Django integration tests use isolated synthetic data and test-only provider mocks."""
import io
from datetime import timedelta, time
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from PIL import Image
from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor, DoctorAvailability
from appointments.models import Appointment
from prescription_reader.models import PrescriptionUpload
from prescription_reader.tasks import process_upload
from prescription_reader.extraction import build_result
import tempfile


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='aihms-tests-'), CELERY_TASK_ALWAYS_EAGER=True)
class PrescriptionReaderAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.a = User.objects.create_user(username='patient_a', email='a@synthetic.example.test', password='Test-only-Aihms-346!', role='patient')
        self.b = User.objects.create_user(username='patient_b', email='b@synthetic.example.test', password='Test-only-Aihms-346!', role='patient')
        self.patient = Patient.objects.create(user=self.a)
        self.client.force_authenticate(self.a)

    def image(self):
        stream = io.BytesIO()
        Image.new('RGB', (300, 300), 'white').save(stream, format='PNG')
        return SimpleUploadedFile('synthetic.png', stream.getvalue(), content_type='image/png')

    def upload(self):
        with patch('prescription_reader.views.enqueue_dispatch'):
            response = self.client.post('/api/prescription-reader/', {'file': self.image(), 'recognition_mode': 'printed'}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        return PrescriptionUpload.objects.get(pk=response.data['id'])

    def test_upload_lifecycle_and_original_preserved(self):
        upload = self.upload()
        original_hash = upload.sha256
        result = build_result([{'page': 1, 'text': 'Medicine: [unreadable]'}], 'test_provider', 1)
        with patch('prescription_reader.providers.process_document', return_value=result):
            process_upload(str(upload.pk))
        upload.refresh_from_db()
        self.assertEqual(upload.status, 'COMPLETED')
        self.assertEqual(upload.sha256, original_hash)
        self.assertEqual(upload.result['fields'][4]['status'], 'unreadable')
        self.assertEqual(self.a.notifications.filter(title='Prescription transcription ready').count(), 1)
        with patch('prescription_reader.providers.process_document') as provider:
            process_upload(str(upload.pk))
            provider.assert_not_called()
        self.assertEqual(self.a.notifications.filter(title='Prescription transcription ready').count(), 1)

    def test_patient_isolation_and_private_files(self):
        upload = self.upload()
        self.client.force_authenticate(self.b)
        response = self.client.get(f'/api/prescription-reader/{upload.pk}/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get('/api/prescription-reader/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/documents/prescription-upload/{upload.pk}/').status_code, 404)
        self.assertEqual(self.client.get('/media/' + upload.file.name).status_code, 404)

    def test_invalid_file_and_unauthorized_upload(self):
        invalid = SimpleUploadedFile('bad.png', b'not an image', content_type='image/png')
        self.assertEqual(self.client.post('/api/prescription-reader/', {'file': invalid}, format='multipart').status_code, 400)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post('/api/prescription-reader/', {'file': self.image()}, format='multipart').status_code, 401)

    def test_provider_unavailable_and_retry(self):
        from prescription_reader.providers import ProviderUnavailable
        upload = self.upload()
        with patch('prescription_reader.providers.process_document', side_effect=ProviderUnavailable('No model configured.')):
            process_upload(str(upload.pk))
        upload.refresh_from_db()
        self.assertEqual(upload.status, 'UNAVAILABLE')
        self.assertFalse(upload.result)
        with patch('prescription_reader.views.enqueue_dispatch'):
            response = self.client.post(f'/api/prescription-reader/{upload.pk}/retry/')
        self.assertEqual(response.status_code, 200)
        upload.refresh_from_db()
        self.assertEqual(upload.status, 'PENDING')

    def test_correction_does_not_change_original_result(self):
        upload = self.upload()
        result = build_result([{'page': 1, 'text': 'Medicine: [unreadable]'}], 'test', 1)
        upload.status, upload.result = 'COMPLETED', result
        upload.save()
        response = self.client.post(f'/api/prescription-reader/{upload.pk}/correction/', {'text': 'Personal annotation'})
        self.assertEqual(response.status_code, 201)
        upload.refresh_from_db()
        self.assertEqual(upload.result, result)
        self.assertEqual(upload.corrections.count(), 1)

    def test_review_is_limited_to_treating_doctor(self):
        doctor_user = User.objects.create_user(username='doc', email='doc@synthetic.example.test', role='doctor')
        doctor = Doctor.objects.create(user=doctor_user, specialization='Test', qualification='Synthetic', registration_number='SYNTHETIC-1')
        upload = self.upload()
        self.client.post(f'/api/prescription-reader/{upload.pk}/request-review/')
        self.client.force_authenticate(doctor_user)
        self.assertEqual(self.client.get(f'/api/prescription-reader/{upload.pk}/').status_code, 404)
        Appointment.objects.create(doctor=doctor, patient=self.patient, scheduled_date=timezone.localdate() + timedelta(days=1), scheduled_time=time(10), status='CONFIRMED')
        self.assertEqual(self.client.post(f'/api/prescription-reader/{upload.pk}/review/', {'notes': 'Synthetic review note.'}).status_code, 201)
        response = self.client.get(f'/api/prescription-reader/{upload.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(response.data['file_url']).status_code, 200)
