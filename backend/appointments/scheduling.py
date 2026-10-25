"""Pure slot calculations; hospital-local wall times with UTC-aware 'now'."""
from datetime import datetime, timedelta


def make_slots(day, start, end, duration_minutes):
    if not 1 <= duration_minutes <= 120 or start >= end:
        raise ValueError('Availability must have a valid interval and a 1–120 minute duration.')
    current = datetime.combine(day, start)
    stop = datetime.combine(day, end)
    duration = timedelta(minutes=duration_minutes)
    while current + duration <= stop:
        yield current.time(), duration_minutes
        current += duration


def overlaps(day, time_a, duration_a, time_b, duration_b):
    start_a, start_b = datetime.combine(day, time_a), datetime.combine(day, time_b)
    return start_a < start_b + timedelta(minutes=duration_b) and start_b < start_a + timedelta(minutes=duration_a)
