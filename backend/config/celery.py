import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('aihms')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic schedule — checked every minute for due medicine reminders,
# and once a day for vaccination reminders due within the next 24h.
app.conf.beat_schedule = {
    'recover-prescription-jobs': {'task': 'prescription_reader.tasks.dispatch_pending', 'schedule': 30.0},
    'send-due-medicine-reminders': {
        'task': 'patients.tasks.send_due_medicine_reminders',
        'schedule': crontab(minute='*/1'),
    },
    'send-due-vaccination-reminders': {
        'task': 'patients.tasks.send_due_vaccination_reminders',
        'schedule': crontab(hour=8, minute=0),  # once daily at 8 AM
    },
    'send-appointment-reminders': {
        'task': 'appointments.tasks.send_appointment_reminders',
        'schedule': crontab(minute='*/15'),
    },
}
