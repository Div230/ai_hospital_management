from datetime import datetime
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound, APIException
from doctors.models import Doctor, DoctorAvailability
from .models import Appointment
from .scheduling import make_slots, overlaps

ACTIVE = ('PENDING', 'CONFIRMED')


class SlotConflict(APIException):
    status_code = 409
    default_detail = 'The selected slot has already been booked.'


def available_slots(doctor, day):
    booked = list(Appointment.objects.filter(doctor=doctor, scheduled_date=day, status__in=ACTIVE))
    now = timezone.localtime()
    slots = {}
    for schedule in DoctorAvailability.objects.filter(doctor=doctor, weekday=day.weekday(), is_active=True):
        for start, duration in make_slots(day, schedule.start_time, schedule.end_time, schedule.slot_duration_minutes):
            if timezone.make_aware(datetime.combine(day, start)) <= now:
                continue
            if not any(overlaps(day, start, duration, a.scheduled_time, a.duration_minutes) for a in booked):
                slots[start.isoformat()] = duration
    return slots


def book_locked(patient, doctor, data):
    # Caller must lock the doctor row in an atomic transaction. This serializes
    # all booking/rescheduling operations even when the original slot is empty.
    if not doctor.is_verified or not doctor.user.is_active:
        raise NotFound('Doctor is not available for booking.')
    duration = available_slots(doctor, data['scheduled_date']).get(data['scheduled_time'].isoformat())
    if duration is None:
        if Appointment.objects.filter(doctor=doctor, scheduled_date=data['scheduled_date'],
                                      scheduled_time=data['scheduled_time'], status__in=ACTIVE).exists():
            raise SlotConflict()
        raise ValidationError({'scheduled_time': 'Select an available future slot from this doctor’s schedule.'})
    if data.get('mode') == 'VIDEO' and not doctor.is_available_for_video:
        raise ValidationError({'mode': 'This doctor does not offer video consultations.'})
    return Appointment.objects.create(patient=patient, doctor=doctor, hospital=doctor.hospital,
                                      duration_minutes=duration, scheduled_date=data['scheduled_date'],
                                      scheduled_time=data['scheduled_time'], mode=data.get('mode', 'IN_PERSON'),
                                      reason=data.get('reason', ''), status='CONFIRMED')


@transaction.atomic
def book(patient, data):
    try:
        doctor = Doctor.objects.select_for_update().select_related('user').get(pk=data['doctor_id'])
    except Doctor.DoesNotExist:
        raise NotFound('Doctor not found.')
    return book_locked(patient, doctor, data)


@transaction.atomic
def reschedule(user, pk, data):
    old = Appointment.objects.filter(pk=pk, patient__user=user).first()
    if not old:
        raise NotFound()
    doctor = Doctor.objects.select_for_update().select_related('user').get(pk=old.doctor_id)
    old = Appointment.objects.select_for_update().get(pk=old.pk)
    if old.status not in ACTIVE:
        raise ValidationError('Only active appointments can be rescheduled.')
    old.status = 'RESCHEDULED'
    old.save(update_fields=['status', 'updated_at'])
    new = book_locked(old.patient, doctor, {**data, 'mode': old.mode, 'reason': old.reason})
    new.rescheduled_from = old
    new.save(update_fields=['rescheduled_from'])
    return new


@transaction.atomic
def cancel(user, pk, reason=''):
    appointment = Appointment.objects.filter(pk=pk).first()
    if not appointment:
        raise NotFound()
    Doctor.objects.select_for_update().get(pk=appointment.doctor_id)
    appointment = Appointment.objects.select_for_update(of=('self',)).select_related('patient__user', 'doctor__user', 'hospital').get(pk=pk)
    allowed = ((user.role == 'patient' and appointment.patient.user_id == user.pk) or
               (user.role == 'doctor' and appointment.doctor.user_id == user.pk))
    if not allowed:
        raise NotFound()
    if appointment.status not in ACTIVE:
        raise ValidationError('Only active appointments can be cancelled.')
    appointment.status, appointment.cancelled_reason = 'CANCELLED', reason[:2000]
    appointment.save(update_fields=['status', 'cancelled_reason', 'updated_at'])
    return appointment
