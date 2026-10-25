import uuid
from django.db import models


class Notification(models.Model):
    CHANNEL_CHOICES = (('EMAIL', 'Email'), ('WHATSAPP', 'WhatsApp'), ('PUSH', 'Push'), ('SMS', 'SMS'))
    TYPE_CHOICES = (
        ('APPOINTMENT_REMINDER', 'Appointment Reminder'),
        ('APPOINTMENT_CONFIRMED', 'Appointment Confirmed'),
        ('APPOINTMENT_CANCELLED', 'Appointment Cancelled'),
        ('MEDICINE_REMINDER', 'Medicine Reminder'),
        ('VACCINATION_REMINDER', 'Vaccination Reminder'),
        ('LAB_REPORT_READY', 'Lab Report Ready'),
        ('PRESCRIPTION_UPDATE', 'Prescription Update'),
        ('SOS_ALERT', 'SOS Alert'),
        ('ORDER_UPDATE', 'Pharmacy Order Update'),
        ('GENERAL', 'General'),
    )
    STATUS_CHOICES = (('PENDING', 'Pending'), ('SENT', 'Sent'), ('FAILED', 'Failed'))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    external_id = models.CharField(max_length=100, blank=True, help_text='Twilio message SID etc.')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_read']), models.Index(fields=['external_id'])]

    def __str__(self):
        return f'[{self.channel}] {self.title} -> {self.user}'


class WebhookSubscription(models.Model):
    """
    Outbound webhooks — lets a hospital's own systems (or a third-party
    integration) subscribe to platform events (e.g. appointment booked,
    lab report ready) and receive an HTTP POST when they happen.
    """
    EVENT_CHOICES = (
        ('APPOINTMENT_BOOKED', 'Appointment Booked'),
        ('APPOINTMENT_CANCELLED', 'Appointment Cancelled'),
        ('LAB_REPORT_READY', 'Lab Report Ready'),
        ('PRESCRIPTION_ISSUED', 'Prescription Issued'),
        ('SOS_TRIGGERED', 'SOS Triggered'),
        ('ORDER_STATUS_CHANGED', 'Pharmacy Order Status Changed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='webhook_subscriptions')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    target_url = models.URLField()
    secret = models.CharField(max_length=64, blank=True, help_text='Used to sign the payload (HMAC-SHA256)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.event_type} -> {self.target_url}'


class WebhookDeliveryLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    subscription = models.ForeignKey(WebhookSubscription, on_delete=models.CASCADE, related_name='delivery_logs')
    payload = models.JSONField(default=dict)
    response_status = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class PushSubscription(models.Model):
    """
    A browser's Web Push subscription (from the PushManager API), stored so
    the backend can send real push notifications even when the app/tab is
    closed. One user can have multiple (one per browser/device).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh_key = models.CharField(max_length=200)
    auth_key = models.CharField(max_length=100)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Push subscription for {self.user}'
