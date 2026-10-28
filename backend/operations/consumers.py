import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

logger = logging.getLogger(__name__)


class LiveOperationsConsumer(AsyncJsonWebsocketConsumer):
    """
    Live real-time WebSocket consumer for ShiftSync:
    - Broadcasts instant notifications (handovers submitted, custody acknowledged, safety alerts)
    - Updates unread notification counters in real time without client polling
    - Notifies incoming/outgoing workers of duty assignment changes
    """

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            logger.warning("Rejected unauthenticated WebSocket connection attempt.")
            await self.close(code=4001)
            return

        self.user = user
        self.user_group = f"user_{self.user.id}"
        self.org_group = f"org_{self.user.organisation_id}"

        # Join personal user group and organisation group
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.org_group, self.channel_name)

        await self.accept()
        logger.info(f"WebSocket connected for user {self.user.email} (ID: {self.user.id})")

        # Send initial handshake confirmation
        await self.send_json({
            "type": "SYSTEM_CONNECTED",
            "message": f"Live telemetry and notification channel connected for {self.user.full_name}",
            "timestamp": timezone.now().isoformat(),
            "user": {
                "id": str(self.user.id),
                "email": self.user.email,
                "role": self.user.role,
            },
        })

    async def disconnect(self, close_code):
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if hasattr(self, "org_group"):
            await self.channel_layer.group_discard(self.org_group, self.channel_name)
        logger.info(f"WebSocket disconnected (code: {close_code})")

    async def receive_json(self, content):
        """Handles client-sent messages, such as keepalive pings."""
        msg_type = content.get("type")
        if msg_type == "PING":
            await self.send_json({
                "type": "PONG",
                "timestamp": timezone.now().isoformat(),
            })

    async def broadcast_event(self, event):
        """Handler for events pushed through the channel layer."""
        await self.send_json(event["payload"])
