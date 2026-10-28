import asyncio
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def push_ws_event_to_user(user_id, event_type: str, data: dict):
    """Dispatches a real-time event to a specific user's active WebSocket connection(s)."""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        group_name = f"user_{user_id}"
        payload = {
            "type": "broadcast_event",
            "payload": {
                "event": event_type,
                "data": data,
            },
        }

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(channel_layer.group_send(group_name, payload))
        else:
            async_to_sync(channel_layer.group_send)(group_name, payload)
    except Exception as e:
        logger.warning(f"Failed to push WS event to user {user_id}: {e}")


def push_ws_event_to_org(org_id, event_type: str, data: dict):
    """Dispatches a real-time event to all connected users within an organisation."""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        group_name = f"org_{org_id}"
        payload = {
            "type": "broadcast_event",
            "payload": {
                "event": event_type,
                "data": data,
            },
        }

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(channel_layer.group_send(group_name, payload))
        else:
            async_to_sync(channel_layer.group_send)(group_name, payload)
    except Exception as e:
        logger.warning(f"Failed to push WS event to org {org_id}: {e}")
