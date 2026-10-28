import pytest
from datetime import date, time
from rest_framework.test import APIClient

from accounts.models import Organisation, User, UserRole
from operations.models import Shift, ShiftStatus


@pytest.fixture
def org_alpha(db):
    return Organisation.objects.create(
        name="Alpha Aviation Services",
        code="ALPHA-OPS",
        departments=["Line Maintenance", "Avionics"],
    )


@pytest.fixture
def org_beta(db):
    return Organisation.objects.create(
        name="Beta Maritime Logistics",
        code="BETA-PORT",
        departments=["Dock Operations"],
    )


@pytest.fixture
def users(org_alpha, org_beta):
    pw = "ShiftSync@2026!"
    admin = User.objects.create_user(
        email="admin@alpha.test",
        full_name="Alpha Admin",
        password=pw,
        role=UserRole.ADMIN,
        organisation=org_alpha,
        department="IT",
        is_staff=True,
    )
    supervisor = User.objects.create_user(
        email="supervisor@alpha.test",
        full_name="Alpha Supervisor",
        password=pw,
        role=UserRole.SUPERVISOR,
        organisation=org_alpha,
        department="Quality",
    )
    outgoing = User.objects.create_user(
        email="outgoing@alpha.test",
        full_name="Alpha Outgoing",
        password=pw,
        role=UserRole.OUTGOING_WORKER,
        organisation=org_alpha,
        department="Line Maintenance",
    )
    incoming = User.objects.create_user(
        email="incoming@alpha.test",
        full_name="Alpha Incoming",
        password=pw,
        role=UserRole.INCOMING_WORKER,
        organisation=org_alpha,
        department="Line Maintenance",
    )
    external = User.objects.create_user(
        email="external@beta.test",
        full_name="Beta External Worker",
        password=pw,
        role=UserRole.INCOMING_WORKER,
        organisation=org_beta,
        department="Dock Operations",
    )
    return {
        "admin": admin,
        "supervisor": supervisor,
        "outgoing": outgoing,
        "incoming": incoming,
        "external": external,
        "password": pw,
    }


@pytest.mark.django_db
class TestAuthenticationAndRBAC:
    def test_valid_login_and_refresh_flow(self, users):
        client = APIClient()
        res = client.post(
            "/api/auth/login/",
            {"email": "outgoing@alpha.test", "password": users["password"]},
            format="json",
        )
        assert res.status_code == 200
        assert "access" in res.data
        assert res.data["user"]["role"] == UserRole.OUTGOING_WORKER
        assert "shiftsync_refresh_token" in res.cookies

        # Refresh access token
        refresh_res = client.post(
            "/api/auth/refresh/",
            {"refresh": res.data["refresh"]},
            format="json",
        )
        assert refresh_res.status_code == 200
        assert "access" in refresh_res.data

    def test_invalid_login_rejected(self, users):
        client = APIClient()
        res = client.post(
            "/api/auth/login/",
            {"email": "outgoing@alpha.test", "password": "WrongPassword123!"},
            format="json",
        )
        assert res.status_code == 401

    def test_deactivated_account_blocked(self, users):
        users["outgoing"].is_active = False
        users["outgoing"].save()
        client = APIClient()
        res = client.post(
            "/api/auth/login/",
            {"email": "outgoing@alpha.test", "password": users["password"]},
            format="json",
        )
        assert res.status_code == 403

    def test_password_recovery_and_reset_flow(self, users):
        client = APIClient()
        rec = client.post(
            "/api/auth/password-recovery/",
            {"email": "outgoing@alpha.test"},
            format="json",
        )
        assert rec.status_code == 200
        token = rec.data.get("reset_token")
        assert token

        new_pw = "UpdatedSecure#2026!"
        reset_res = client.post(
            "/api/auth/password-reset/",
            {"token": token, "new_password": new_pw},
            format="json",
        )
        assert reset_res.status_code == 200

        login_res = client.post(
            "/api/auth/login/",
            {"email": "outgoing@alpha.test", "password": new_pw},
            format="json",
        )
        assert login_res.status_code == 200

    def test_only_admin_can_provision_users_and_shifts(self, users):
        client = APIClient()
        # Supervisor cannot create a user
        client.force_authenticate(user=users["supervisor"])
        res_sup = client.post(
            "/api/users/",
            {
                "email": "new@alpha.test",
                "full_name": "New Worker",
                "role": UserRole.OUTGOING_WORKER,
                "department": "Line Maintenance",
                "password": "ShiftSync@2026!",
            },
            format="json",
        )
        assert res_sup.status_code == 403

        # Admin can create a user and assign a shift
        client.force_authenticate(user=users["admin"])
        res_adm = client.post(
            "/api/users/",
            {
                "email": "new@alpha.test",
                "full_name": "New Worker",
                "role": UserRole.OUTGOING_WORKER,
                "department": "Line Maintenance",
                "password": "ShiftSync@2026!",
            },
            format="json",
        )
        assert res_adm.status_code == 201

        shift_res = client.post(
            "/api/shifts/",
            {
                "name": "Morning Shift 01",
                "department": "Line Maintenance",
                "shift_date": str(date.today()),
                "start_time": "06:00:00",
                "end_time": "14:00:00",
                "outgoing_worker": str(users["outgoing"].id),
                "incoming_worker": str(users["incoming"].id),
                "supervisor": str(users["supervisor"].id),
                "status": ShiftStatus.ACTIVE,
            },
            format="json",
        )
        assert shift_res.status_code == 201

    def test_cross_organisation_data_isolation(self, users, org_alpha):
        shift = Shift.objects.create(
            organisation=org_alpha,
            name="Alpha Secret Shift",
            shift_date=date.today(),
            start_time=time(6, 0),
            end_time=time(14, 0),
            outgoing_worker=users["outgoing"],
            incoming_worker=users["incoming"],
            status=ShiftStatus.ACTIVE,
        )
        client = APIClient()
        client.force_authenticate(user=users["external"])
        # External user in Beta org cannot see Alpha org shifts
        res = client.get("/api/shifts/")
        assert res.status_code == 200
        assert res.data["count"] == 0
        detail_res = client.get(f"/api/shifts/{shift.id}/")
        assert detail_res.status_code == 404

    def test_health_check_unauthenticated(self, db):
        client = APIClient()
        res = client.get("/api/health/")
        assert res.status_code == 200
        assert res.data["status"] == "ok"
        assert res.data["database"] == "up"
        assert "timestamp" in res.data

