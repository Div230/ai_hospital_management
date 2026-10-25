import uuid
from django.db import migrations, models
import django.db.models.deletion
import prescription_reader.models


class Migration(migrations.Migration):
    initial = True
    dependencies = [('patients', '0001_initial'), ('doctors', '0001_initial')]
    operations = [
        migrations.CreateModel(name='PrescriptionUpload', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('file', models.FileField(upload_to=prescription_reader.models.private_upload_path)),
            ('original_filename', models.CharField(max_length=200)),
            ('mime_type', models.CharField(max_length=50)),
            ('size_bytes', models.PositiveIntegerField()),
            ('sha256', models.CharField(max_length=64)),
            ('recognition_mode', models.CharField(max_length=15, choices=[('printed', 'Printed'), ('handwritten', 'Handwritten')])),
            ('external_consent', models.BooleanField(default=False)),
            ('status', models.CharField(max_length=20, db_index=True, default='PENDING', choices=[
                ('PENDING', 'Waiting for worker'), ('QUEUED', 'Queued'), ('PROCESSING', 'Processing'),
                ('COMPLETED', 'Transcription available'), ('FAILED', 'Processing failed'), ('UNAVAILABLE', 'Recognition service unavailable')])),
            ('result', models.JSONField(default=dict, blank=True)),
            ('error_code', models.CharField(max_length=50, blank=True)),
            ('error_message', models.CharField(max_length=300, blank=True)),
            ('attempt_count', models.PositiveSmallIntegerField(default=0)),
            ('lease_until', models.DateTimeField(null=True, blank=True)),
            ('run_token', models.UUIDField(null=True, blank=True)),
            ('review_requested_at', models.DateTimeField(null=True, blank=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('patient', models.ForeignKey(to='patients.patient', on_delete=django.db.models.deletion.PROTECT, related_name='prescription_uploads')),
        ], options={'ordering': ['-created_at'], 'indexes': [models.Index(fields=['patient', '-created_at'], name='rx_patient_created_idx')]}),
        migrations.CreateModel(name='PersonalCorrection', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('text', models.TextField()), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('upload', models.ForeignKey(to='prescription_reader.prescriptionupload', on_delete=django.db.models.deletion.PROTECT, related_name='corrections')),
        ], options={'ordering': ['-created_at', '-pk']}),
        migrations.CreateModel(name='ClinicianReview', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('notes', models.TextField()), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('doctor', models.ForeignKey(to='doctors.doctor', on_delete=django.db.models.deletion.PROTECT)),
            ('upload', models.ForeignKey(to='prescription_reader.prescriptionupload', on_delete=django.db.models.deletion.PROTECT, related_name='reviews')),
        ], options={'ordering': ['-created_at', '-pk']}),
    ]
