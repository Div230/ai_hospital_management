from rest_framework import generics, permissions, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from core.permissions import IsHospitalAdmin
from django.conf import settings
from .models import Notification, WebhookSubscription, PushSubscription
from .serializers import NotificationSerializer, WebhookSubscriptionSerializer, WebhookDeliveryLogSerializer, PushSubscriptionSerializer


class MyNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_read', 'channel', 'notification_type']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'success': False, 'message': 'Not found.'}, status=404)
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'success': True})


class WebhookSubscriptionViewSet(viewsets.ModelViewSet):
    """Lets a hospital admin register outbound webhooks for platform events."""
    serializer_class = WebhookSubscriptionSerializer
    permission_classes = [IsHospitalAdmin]

    def get_queryset(self):
        return WebhookSubscription.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@method_decorator(csrf_exempt, name='dispatch')
class TwilioStatusWebhookView(APIView):
    """
    Inbound webhook — Twilio POSTs delivery status updates here
    (queued/sent/delivered/failed/undelivered) for WhatsApp messages we sent.
    Configure this URL as the `StatusCallback` on your Twilio message calls.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not settings.OUTBOUND_NOTIFICATIONS_ENABLED or not settings.TWILIO_AUTH_TOKEN:
            return Response({'message': 'Twilio integration unavailable.'}, status=503)
        from twilio.request_validator import RequestValidator
        if not RequestValidator(settings.TWILIO_AUTH_TOKEN).validate(request.build_absolute_uri(), request.data, request.headers.get('X-Twilio-Signature', '')):
            return Response({'message': 'Invalid webhook signature.'}, status=403)
        message_sid = request.data.get('MessageSid') or request.data.get('SmsSid')
        message_status = request.data.get('MessageStatus') or request.data.get('SmsStatus')

        if not message_sid:
            return Response({'success': False, 'message': 'Missing MessageSid.'}, status=400)

        updated = Notification.objects.filter(external_id=message_sid).update(
            status='SENT' if message_status in ('sent', 'delivered') else
                   'FAILED' if message_status in ('failed', 'undelivered') else 'PENDING',
        )
        return Response({'success': True, 'updated': updated})


class VapidPublicKeyView(APIView):
    """Frontend fetches this once to know which VAPID public key to use
    when calling PushManager.subscribe()."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({'public_key': settings.VAPID_PUBLIC_KEY})


class PushSubscriptionView(APIView):
    """
    POST: browser registers its PushManager subscription here (called after
    the user grants Notification permission and subscribes on the frontend).
    DELETE: unregister (e.g. on logout / disabling notifications).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get('endpoint')
        keys = request.data.get('keys', {})
        if not endpoint or not keys.get('p256dh') or not keys.get('auth'):
            return Response({'success': False, 'message': 'Invalid subscription payload.'}, status=400)

        sub, _ = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': request.user,
                'p256dh_key': keys['p256dh'],
                'auth_key': keys['auth'],
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:255],
            },
        )
        return Response({'success': True, 'data': PushSubscriptionSerializer(sub).data}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        endpoint = request.data.get('endpoint')
        deleted, _ = PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return Response({'success': True, 'deleted': deleted})
