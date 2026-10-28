import pytest
from datetime import date, time
from rest_framework.test import APIClient

from accounts.models import Organisation, User, UserRole
from operations.models import (
    HandoverReport,
    HandoverStatus,
    Shift,
    ShiftStatus,
    Task,
    TaskPriority,
    TaskStatus,
)


@pytest.fixture
def setup_workflow(db):
    org = Organisation.objects.create(name="ShiftSync Test Org", code="TEST-ORG")
    pw = "ShiftSync@2026!"
    admin = User.objects.create_user(
        email="admin@test.org",
        full_name="Test Admin",
        password=pw,
        role=UserRole.ADMIN,
        organisation=org,
    )
    supervisor = User.objects.create_user(
        email="sup@test.org",
        full_name="Test Supervisor",
        password=pw,
        role=UserRole.SUPERVISOR,
        organisation=org,
    )
    outgoing = User.objects.create_user(
        email="out@test.org",
        full_name="Test Outgoing",
        password=pw,
        role=UserRole.OUTGOING_WORKER,
        organisation=org,
    )
    incoming = User.objects.create_user(
        email="inc@test.org",
        full_name="Test Incoming",
        password=pw,
        role=UserRole.INCOMING_WORKER,
        organisation=org,
    )
    other_incoming = User.objects.create_user(
        email="inc2@test.org",
        full_name="Other Incoming",
        password=pw,
        role=UserRole.INCOMING_WORKER,
        organisation=org,
    )
    shift = Shift.objects.create(
        organisation=org,
        name="Line Maintenance Shift A",
        shift_date=date.today(),
        start_time=time(6, 0),
        end_time=time(14, 0),
        outgoing_worker=outgoing,
        incoming_worker=incoming,
        supervisor=supervisor,
        status=ShiftStatus.ACTIVE,
    )
    return {
        "org": org,
        "admin": admin,
        "supervisor": supervisor,
        "outgoing": outgoing,
        "incoming": incoming,
        "other_incoming": other_incoming,
        "shift": shift,
    }


@pytest.mark.django_db
class TestHandoverLifecycleAndAcknowledgment:
    def test_complete_draft_submit_acknowledge_and_carry_forward_workflow(
        self, setup_workflow
    ):
        env = setup_workflow
        client = APIClient()

        # 1. Outgoing worker creates a Draft handover with NLP suggestions and manual override
        client.force_authenticate(user=env["outgoing"])
        create_res = client.post(
            "/api/handovers/",
            {
                "shift": str(env["shift"].id),
                "designated_incoming_worker": str(env["incoming"].id),
                "equipment_status": "MINOR_ISSUE",
                "equipment_details": "Hydraulic rig #2 gauge slightly sticky.",
                "safety_issues": "Wet floor near hangar door B; warning cones placed.",
                "has_safety_incident": True,
                "additional_notes": "Initial draft notes.",
                "tasks_input": [
                    {
                        "description": "Inspect boiler pressure valve on Line 2 after fluctuating readings.",
                        "status": "Pending",
                        "model_suggested_category": "Equipment Check",
                        "model_suggested_priority": "Medium",
                        "category_confidence": 91.2,
                        "priority_confidence": 78.4,
                        "confidence_score": 84.8,
                        "confirmed_category": "Equipment Check",
                        "confirmed_priority": "Critical",
                        "contextual_notes": "Upgraded priority to Critical manually.",
                    },
                    {
                        "description": "Completed routine pre-flight instrument scan on 5Y-KZE.",
                        "status": "Completed",
                        "model_suggested_category": "Equipment Check",
                        "model_suggested_priority": "Medium",
                        "confirmed_category": "Equipment Check",
                        "confirmed_priority": "Medium",
                    },
                ],
            },
            format="json",
        )
        assert create_res.status_code == 201
        handover_id = create_res.data["id"]
        assert create_res.data["status"] == HandoverStatus.DRAFT
        assert len(create_res.data["tasks"]) == 2

        # Verify manual override was tracked on task 1
        crit_task = next(
            t for t in create_res.data["tasks"] if t["confirmed_priority"] == "Critical"
        )
        assert crit_task["was_overridden"] is True
        assert crit_task["model_suggested_priority"] == "Medium"

        # 2. Outgoing worker edits the draft before submitting
        patch_res = client.patch(
            f"/api/handovers/{handover_id}/",
            {"additional_notes": "Updated draft notes before formal submission."},
            format="json",
        )
        assert patch_res.status_code == 200
        assert (
            patch_res.data["additional_notes"]
            == "Updated draft notes before formal submission."
        )

        # 3. Outgoing worker formally submits the handover
        sub_res = client.post(f"/api/handovers/{handover_id}/submit/", {}, format="json")
        assert sub_res.status_code == 200
        assert sub_res.data["status"] == HandoverStatus.SUBMITTED
        assert sub_res.data["submitted_at"] is not None

        # 4. Duplicate submission is prevented
        dup_res = client.post(f"/api/handovers/{handover_id}/submit/", {}, format="json")
        assert dup_res.status_code == 400

        # 5. Ordinary editing of a submitted report is prevented
        edit_locked_res = client.patch(
            f"/api/handovers/{handover_id}/",
            {"additional_notes": "Silent rewrite attempt"},
            format="json",
        )
        assert edit_locked_res.status_code == 400

        # 6. Viewing the report as the incoming worker does NOT acknowledge it
        client.force_authenticate(user=env["incoming"])
        view_res = client.get(f"/api/handovers/{handover_id}/")
        assert view_res.status_code == 200
        assert view_res.data["status"] == HandoverStatus.SUBMITTED
        assert view_res.data["acknowledged_at"] is None

        # 7. An unassigned incoming worker cannot acknowledge someone else's handover
        client.force_authenticate(user=env["other_incoming"])
        unauth_ack = client.post(
            f"/api/handovers/{handover_id}/acknowledge/",
            {"acknowledgment_notes": "Trying to sign off someone else's handover"},
            format="json",
        )
        assert unauth_ack.status_code == 403

        # 8. Designated incoming worker explicitly acknowledges receipt
        client.force_authenticate(user=env["incoming"])
        ack_res = client.post(
            f"/api/handovers/{handover_id}/acknowledge/",
            {"acknowledgment_notes": "Reviewed and accepted responsibility for Line 2 valve."},
            format="json",
        )
        assert ack_res.status_code == 200
        assert ack_res.data["status"] == HandoverStatus.ACKNOWLEDGED
        assert str(ack_res.data["acknowledged_by"]) == str(env["incoming"].id)
        assert ack_res.data["acknowledged_at"] is not None
        assert len(ack_res.data["acknowledgment_events"]) == 1

        # 9. Unfinished task remains Pending (NOT marked Completed) and is marked carried forward
        pending_task = Task.objects.get(id=crit_task["id"])
        assert pending_task.status == TaskStatus.PENDING
        assert pending_task.is_carried_forward is True

        # 10. Supervisor dashboard reflects actual database counts
        client.force_authenticate(user=env["supervisor"])
        dash_res = client.get("/api/analytics/dashboard/")
        assert dash_res.status_code == 200
        metrics = dash_res.data["metrics"]
        assert metrics["acknowledged_handovers"] == 1
        assert metrics["unresolved_tasks"] == 1
        assert metrics["critical_priority_tasks"] == 1
        assert metrics["handover_completion_rate"] == 100.0
