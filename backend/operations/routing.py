from django.urls import re_path
from .consumers import LiveOperationsConsumer

websocket_urlpatterns = [
    re_path(r"^ws/live/?$", LiveOperationsConsumer.as_asgi()),
]
