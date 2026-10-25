from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MyNotificationsView, MarkNotificationReadView, WebhookSubscriptionViewSet,
    TwilioStatusWebhookView, VapidPublicKeyView, PushSubscriptionView,
)

app_name = 'notifications'

router = DefaultRouter()
router.register('webhook-subscriptions', WebhookSubscriptionViewSet, basename='webhook-subscription')

urlpatterns = [
    path('', MyNotificationsView.as_view(), name='list'),
    path('<uuid:pk>/read/', MarkNotificationReadView.as_view(), name='mark_read'),
    path('webhooks/twilio-status/', TwilioStatusWebhookView.as_view(), name='twilio_status_webhook'),
    path('push/vapid-public-key/', VapidPublicKeyView.as_view(), name='vapid_public_key'),
    path('push/subscribe/', PushSubscriptionView.as_view(), name='push_subscribe'),
    path('', include(router.urls)),
]
