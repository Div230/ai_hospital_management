from django.db import migrations, models


def fail_on_duplicate_slots(apps, schema_editor):
    Appointment = apps.get_model('appointments', 'Appointment')
    duplicates = (Appointment.objects.filter(status__in=['PENDING', 'CONFIRMED'], is_deleted=False)
                  .values('doctor_id', 'scheduled_date', 'scheduled_time').annotate(n=models.Count('id')).filter(n__gt=1))
    if duplicates.exists():
        raise RuntimeError('Resolve duplicate active appointments before applying booking integrity migration.')


class Migration(migrations.Migration):
    dependencies = [('appointments', '0002_initial')]
    operations = [
        migrations.AddField(model_name='appointment', name='duration_minutes', field=models.PositiveSmallIntegerField(default=15)),
        migrations.RunPython(fail_on_duplicate_slots, migrations.RunPython.noop),
        migrations.AddConstraint(model_name='appointment', constraint=models.UniqueConstraint(
            fields=['doctor', 'scheduled_date', 'scheduled_time'],
            condition=models.Q(status__in=['PENDING', 'CONFIRMED'], is_deleted=False), name='unique_active_doctor_slot')),
        migrations.AddConstraint(model_name='appointment', constraint=models.CheckConstraint(
            condition=models.Q(duration_minutes__gte=1, duration_minutes__lte=120), name='valid_appointment_duration')),
    ]
