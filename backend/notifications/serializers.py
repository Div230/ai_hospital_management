from rest_framework import serializers
from .models import Notification, WebhookSubscription, WebhookDeliveryLog, PushSubscription


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'user', 'status', 'sent_at', 'created_at']


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookSubscription
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'owner', 'created_at']


class WebhookDeliveryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDeliveryLog
        fields = '__all__'


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'user', 'created_at']
