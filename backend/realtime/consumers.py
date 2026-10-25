"""
WebSocket consumers for real-time features:
  - AmbulanceTrackingConsumer: live location broadcast for an SOS ambulance
  - VideoCallConsumer: WebRTC signaling relay (offer/answer/ICE candidates)
    for a doctor-patient video consultation tied to one appointment.

Auth: the frontend connects with ?token=<JWT access token> in the query
string (browsers can't set custom headers on a WebSocket handshake), which
AuthMiddlewareStack-adjacent code in middleware.py resolves to request.user.
"""
import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger('healthcare')


class AmbulanceTrackingConsumer(AsyncJsonWebsocketConsumer):
    """
    Group name: ambulance_<ambulance_id>
    - The ambulance/driver side (or, in this demo, a simulator) sends
      {"type": "location_update", "latitude": .., "longitude": .., "eta_minutes": ..}
    - The patient side just listens and receives location_update broadcasts.
    Anyone connected to this group receives every update — simplest possible
    real-time model for a demo; a production build would separate driver
    vs. rider permissions.
    """

    async def connect(self):
        self.ambulance_id = self.scope['url_route']['kwargs']['ambulance_id']
        self.group_name = f'ambulance_{self.ambulance_id}'

        user = self.scope.get('user')
        if user is None or not getattr(user, 'is_authenticated', False):
            await self.close(code=4001)
            return

        from channels.db import database_sync_to_async
        from patients.models import AmbulanceRequest
        if not await database_sync_to_async(AmbulanceRequest.objects.filter(pk=self.ambulance_id, sos_alert__patient__user=user).exists)():
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'ambulance_id': self.ambulance_id})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Patient connections only receive tracking; dispatch integrations own updates.
        await self.close(code=4003)

    async def broadcast_location(self, event):
        await self.send_json({
            'type': 'location_update',
            'latitude': event.get('latitude'),
            'longitude': event.get('longitude'),
            'eta_minutes': event.get('eta_minutes'),
            'status': event.get('status'),
        })

    @staticmethod
    def _sync_save_location(ambulance_id, content):
        from patients.models import AmbulanceRequest
        AmbulanceRequest.objects.filter(id=ambulance_id).update(
            current_latitude=content.get('latitude'),
            current_longitude=content.get('longitude'),
            eta_minutes=content.get('eta_minutes'),
            status=content.get('status') or 'EN_ROUTE',
        )

    async def _save_location(self, content):
        from channels.db import database_sync_to_async
        await database_sync_to_async(self._sync_save_location)(self.ambulance_id, content)


class VideoCallConsumer(AsyncJsonWebsocketConsumer):
    """
    WebRTC signaling relay for a video consultation, scoped to one
    appointment (group name: video_<appointment_id>). Only that
    appointment's patient or doctor may join. This consumer never touches
    media itself — it just relays SDP offers/answers and ICE candidates
    between the two peers so their browsers can establish a direct
    peer-to-peer WebRTC connection.
    """

    async def connect(self):
        self.appointment_id = self.scope['url_route']['kwargs']['appointment_id']
        self.group_name = f'video_{self.appointment_id}'
        user = self.scope.get('user')

        if user is None or not getattr(user, 'is_authenticated', False):
            await self.close(code=4001)
            return

        allowed = await self._user_is_participant(user, self.appointment_id)
        if not allowed:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'peer_event', 'event': 'peer_joined', 'sender_channel': self.channel_name},
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_send(
                self.group_name,
                {'type': 'peer_event', 'event': 'peer_left', 'sender_channel': self.channel_name},
            )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Relay signaling messages (offer/answer/ice-candidate) to the other peer(s) in the room
        content['sender_channel'] = self.channel_name
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'relay_signal', 'payload': content},
        )

    async def relay_signal(self, event):
        payload = event['payload']
        # Don't echo a peer's own message back to itself
        if payload.get('sender_channel') == self.channel_name:
            return
        await self.send_json(payload)

    async def peer_event(self, event):
        if event.get('sender_channel') == self.channel_name:
            return
        await self.send_json({'type': event['event']})

    @staticmethod
    def _sync_check_participant(user, appointment_id):
        from appointments.models import Appointment
        try:
            appt = Appointment.objects.select_related('patient__user', 'doctor__user').get(id=appointment_id)
        except Appointment.DoesNotExist:
            return False
        return appt.patient.user_id == user.id or appt.doctor.user_id == user.id

    async def _user_is_participant(self, user, appointment_id):
        from channels.db import database_sync_to_async
        return await database_sync_to_async(self._sync_check_participant)(user, appointment_id)
