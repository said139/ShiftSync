import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Organisation, User, UserRole
from common.ws_broadcast import push_ws_event_to_user, push_ws_event_to_org
from shiftsync_backend.asgi import application


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_websocket_authentication_and_live_events():
    # 1. Setup Organisation and Users
    org = await database_sync_to_async(Organisation.objects.create)(
        name="Kenya Airways WS Ops",
        code="KQ-WS",
        industry="Commercial Aviation",
    )
    user = await database_sync_to_async(User.objects.create_user)(
        email="pilot.ws@kq.ac.ke",
        password="ShiftSync@2026!",
        full_name="Capt. WS Pilot",
        employee_id="KQ-WS-001",
        role=UserRole.OUTGOING_WORKER,
        organisation=org,
    )

    token = await database_sync_to_async(
        lambda: str(RefreshToken.for_user(user).access_token)
    )()

    # 2. Connect with valid JWT token
    communicator = WebsocketCommunicator(
        application,
        f"/ws/live/?token={token}",
        headers=[(b"origin", b"http://127.0.0.1:5173")],
    )
    connected, subprotocol = await communicator.connect()
    assert connected, "WebSocket should connect successfully with valid JWT"

    # 3. Receive SYSTEM_CONNECTED welcome message
    welcome = await communicator.receive_json_from(timeout=5)
    assert welcome["type"] == "SYSTEM_CONNECTED"
    assert welcome["user"]["email"] == "pilot.ws@kq.ac.ke"

    # 4. Send PING and receive PONG
    await communicator.send_json_to({"type": "PING"})
    pong = await communicator.receive_json_from(timeout=5)
    assert pong["type"] == "PONG"

    # 5. Push live broadcast event to user
    push_ws_event_to_user(
        user.id,
        "HANDOVER_SUBMITTED",
        {"report_code": "HND-WS-999", "status": "SUBMITTED"},
    )
    event = await communicator.receive_json_from(timeout=5)
    assert event["event"] == "HANDOVER_SUBMITTED"
    assert event["data"]["report_code"] == "HND-WS-999"

    # 6. Push live broadcast event to organisation
    push_ws_event_to_org(
        org.id,
        "DASHBOARD_METRIC_UPDATE",
        {"metric": "active_shifts", "value": 5},
    )
    org_event = await communicator.receive_json_from(timeout=5)
    assert org_event["event"] == "DASHBOARD_METRIC_UPDATE"
    assert org_event["data"]["value"] == 5

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_websocket_unauthenticated_connection_rejected():
    # Connect without token
    communicator = WebsocketCommunicator(
        application,
        "/ws/live/",
        headers=[(b"origin", b"http://127.0.0.1:5173")],
    )
    connected, _ = await communicator.connect()
    assert not connected, "WebSocket connection without valid JWT must be rejected with close code"
