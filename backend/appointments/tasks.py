import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('healthcare')


@shared_task
def send_appointment_reminders():
    """
    Runs every 15 minutes. Notifies patients of confirmed appointments
    happening within the next hour, and marks them so we don't double-notify.
    """
    from .models import Appointment
    from notifications.services import notify_user

    now = timezone.localtime()
    window_end = now + timedelta(hours=1)

    upcoming = Appointment.objects.filter(
        status='CONFIRMED',
        scheduled_date=now.date(),
        scheduled_time__gte=now.time(),
        scheduled_time__lte=window_end.time(),
    )

    sent_count = 0
    for appt in upcoming:
        already_sent = appt.patient.user.notifications.filter(
            notification_type='APPOINTMENT_REMINDER',
            metadata__appointment_id=str(appt.id),
        ).exists()
        if already_sent:
            continue

        notification = notify_user(
            appt.patient.user, 'APPOINTMENT_REMINDER', 'Appointment Reminder',
            f'Reminder: your appointment with Dr. {appt.doctor.user.get_full_name()} '
            f'is at {appt.scheduled_time} today.',
            channel='WHATSAPP',
        )
        notification.metadata = {'appointment_id': str(appt.id)}
        notification.save(update_fields=['metadata'])
        sent_count += 1

    logger.info(f'Appointment reminders sent: {sent_count}')
    return sent_count
