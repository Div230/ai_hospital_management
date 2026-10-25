import logging
from celery import shared_task
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger('healthcare')


@shared_task
def send_due_medicine_reminders():
    """
    Runs every minute (see config/celery.py beat schedule). Checks every
    active MedicineReminder whose reminder_times list contains the current
    HH:MM, and fires a WhatsApp notification for it.
    """
    from .models import MedicineReminder
    from notifications.services import notify_user

    now = timezone.localtime()
    current_hhmm = now.strftime('%H:%M')
    today = now.date()

    reminders = MedicineReminder.objects.filter(
        is_active=True, start_date__lte=today,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))

    sent_count = 0
    for reminder in reminders:
        if current_hhmm in (reminder.reminder_times or []):
            notify_user(
                reminder.patient.user, 'MEDICINE_REMINDER', 'Medicine Reminder',
                f'Time to take {reminder.medicine_name} ({reminder.dosage}).',
                channel='WHATSAPP',
            )
            sent_count += 1
    logger.info(f'Medicine reminders sent: {sent_count} at {current_hhmm}')
    return sent_count


@shared_task
def send_due_vaccination_reminders():
    """Runs once daily. Notifies patients about vaccinations due within 24h."""
    from datetime import timedelta
    from .models import VaccinationReminder
    from notifications.services import notify_user

    tomorrow = timezone.localdate() + timedelta(days=1)
    due = VaccinationReminder.objects.filter(is_completed=False, scheduled_date=tomorrow)

    sent_count = 0
    for reminder in due:
        notify_user(
            reminder.patient.user, 'VACCINATION_REMINDER', 'Vaccination Reminder',
            f'Reminder: {reminder.vaccine_name} vaccination is scheduled for tomorrow ({reminder.scheduled_date}).',
            channel='WHATSAPP',
        )
        sent_count += 1
    logger.info(f'Vaccination reminders sent: {sent_count}')
    return sent_count
