from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/ambulance/(?P<ambulance_id>[0-9a-f-]+)/$', consumers.AmbulanceTrackingConsumer.as_asgi()),
    re_path(r'^ws/video-call/(?P<appointment_id>[0-9a-f-]+)/$', consumers.VideoCallConsumer.as_asgi()),
]
