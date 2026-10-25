"""
Notification service layer — single place all apps call into for sending
Email / WhatsApp / SMS alerts, plus outbound webhook dispatch. Keeping this
abstracted means swapping Twilio for MSG91 later is a one-file change, not
a codebase-wide refactor.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger('healthcare')


def send_email_notification(to_email, subject, message):
    if not settings.OUTBOUND_NOTIFICATIONS_ENABLED:
        return False, None
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER or 'noreply@aihms.example.test',
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info('Email delivered')
        return True, None
    except Exception as e:
        logger.error('Email delivery failed')
        return False, None


def send_whatsapp_notification(to_phone, message):
    """
    Sends via Twilio WhatsApp API. Falls back to logging in demo mode when
    TWILIO_ACCOUNT_SID isn't configured, so the rest of the app keeps working
    without live credentials.
    Returns (success: bool, twilio_message_sid: str | None).
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return False, None

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            to=f'whatsapp:{to_phone}',
            body=message,
        )
        logger.info(f'WhatsApp sent to {to_phone}, SID={msg.sid}')
        return True, msg.sid
    except Exception as e:
        logger.error(f'WhatsApp send failed to {to_phone}: {e}')
        return False, None


def send_sms_notification(to_phone, message):
    """
    Sends a plain SMS via Twilio (separate from the WhatsApp channel above —
    uses TWILIO_SMS_NUMBER instead of the WhatsApp sender). Falls back to
    logging in demo mode when Twilio isn't configured.
    Returns (success: bool, twilio_message_sid: str | None).
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_SMS_NUMBER:
        return False, None

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            from_=settings.TWILIO_SMS_NUMBER,
            to=to_phone,
            body=message,
        )
        logger.info(f'SMS sent to {to_phone}, SID={msg.sid}')
        return True, msg.sid
    except Exception as e:
        logger.error(f'SMS send failed to {to_phone}: {e}')
        return False, None


def send_push_notification(user, title, message, url='/'):
    """
    Sends a real Web Push notification to every browser subscription this
    user has registered (via PushManager on the frontend). Falls back to
    logging in demo mode if VAPID keys aren't configured.
    Returns True if at least one subscription received it successfully.
    """
    from .models import PushSubscription

    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        return False

    subscriptions = PushSubscription.objects.filter(user=user)
    if not subscriptions.exists():
        logger.info(f'No push subscriptions registered for {user.email}; skipping push send.')
        return False

    import json as _json
    from pywebpush import webpush, WebPushException

    any_success = False
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh_key, 'auth': sub.auth_key},
                },
                data=_json.dumps({'title': title, 'body': message, 'url': url}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={'sub': f'mailto:{settings.VAPID_ADMIN_EMAIL}'},
            )
            any_success = True
        except WebPushException as e:
            logger.warning(f'Push send failed for subscription {sub.id}: {e}')
            # 404/410 means the browser subscription is dead — clean it up
            if e.response is not None and e.response.status_code in (404, 410):
                sub.delete()
        except Exception as e:
            # Malformed subscription data (bad keys, bad endpoint, etc.) should
            # never take down the caller's notify_user() flow — log and move on.
            logger.error(f'Unexpected error sending push to subscription {sub.id}: {e}')
    return any_success


def notify_user(user, notification_type, title, message, channel='EMAIL'):
    """
    High-level helper: creates a Notification row AND actually dispatches it
    over the requested channel (EMAIL / WHATSAPP / SMS). Call this from
    appointments/lab/pharmacy/emergency modules instead of talking to
    email/Twilio directly.

    For WHATSAPP/SMS, the Twilio message SID (if a real send happened) is
    stored on the Notification as `external_id`, so the inbound
    /api/notifications/webhooks/twilio-status/ callback can later match
    Twilio's delivery-status update back to this exact notification.
    """
    from .models import Notification
    from django.utils import timezone

    notification = Notification.objects.create(
        user=user,
        channel=channel,
        notification_type=notification_type,
        title=title,
        message=message,
    )

    if not settings.OUTBOUND_NOTIFICATIONS_ENABLED:
        return notification

    sent = False
    external_id = None

    if channel == 'EMAIL':
        sent, external_id = send_email_notification(user.email, title, message)
    elif channel == 'WHATSAPP' and user.whatsapp_opt_in and user.phone_number:
        sent, external_id = send_whatsapp_notification(user.phone_number, f'{title}\n{message}')
    elif channel == 'SMS' and user.phone_number:
        sent, external_id = send_sms_notification(user.phone_number, f'{title}: {message}')
    elif channel == 'PUSH':
        sent = send_push_notification(user, title, message)
    else:
        # e.g. WHATSAPP requested but user opted out / has no phone number
        logger.warning(f'notify_user: channel {channel} not deliverable for user {user.id} (missing phone/opt-in).')

    if sent:
        notification.status = 'SENT'
        notification.sent_at = timezone.now()
    else:
        notification.status = 'FAILED'
    if external_id:
        notification.external_id = external_id
    notification.save(update_fields=['status', 'sent_at', 'external_id'])

    # Best-effort: also push to any registered browser subscriptions,
    # regardless of the primary channel requested, so real-time in-app
    # alerts work even when the person isn't actively looking at the tab.
    # This does not create a duplicate Notification row — it's purely a
    # delivery mechanism layered on top of the one already created above.
    if channel != 'PUSH':
        try:
            from .models import PushSubscription
            if PushSubscription.objects.filter(user=user).exists():
                send_push_notification(user, title, message)
        except Exception as e:
            logger.error(f'Auto-push side effect failed (non-fatal): {e}')

    return notification


def dispatch_webhook_event(owner, event_type, payload):
    """
    Fires an HTTP POST to every active WebhookSubscription matching this
    event type. If `owner` (a specific Hospital Admin user) is given, only
    that owner's subscriptions fire — used for events that are clearly tied
    to one hospital (appointments, prescriptions). If `owner` is None, ALL
    active subscriptions for this event type fire regardless of hospital —
    used for events that aren't tied to a single hospital in the current
    schema (lab reports, SOS, pharmacy orders). Payload is HMAC-signed if
    the subscription has a secret configured.
    """
    import hmac
    import hashlib
    import json as _json
    import requests
    from .models import WebhookSubscription, WebhookDeliveryLog

    if not settings.OUTBOUND_WEBHOOKS_ENABLED or owner is None:
        return
    subscriptions = WebhookSubscription.objects.filter(event_type=event_type, is_active=True)
    if owner is not None:
        subscriptions = subscriptions.filter(owner=owner)

    for sub in subscriptions:
        body = _json.dumps(payload, default=str)
        headers = {'Content-Type': 'application/json'}
        if sub.secret:
            signature = hmac.new(sub.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            headers['X-Webhook-Signature'] = signature

        try:
            resp = requests.post(sub.target_url, data=body, headers=headers, timeout=5)
            WebhookDeliveryLog.objects.create(
                subscription=sub, payload=payload,
                response_status=resp.status_code, success=resp.ok,
            )
        except Exception as e:
            logger.error(f'Webhook delivery failed for {sub.target_url}: {e}')
            WebhookDeliveryLog.objects.create(
                subscription=sub, payload=payload, success=False, error_message=str(e),
            )
