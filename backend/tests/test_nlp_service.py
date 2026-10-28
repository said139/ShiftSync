import pytest
from rest_framework.test import APIClient

from accounts.models import Organisation, User, UserRole
from nlp_service.engine import ShiftSyncNLPService


@pytest.fixture
def nlp_user(db):
    org = Organisation.objects.create(name="NLP Test Org", code="NLP-ORG")
    return User.objects.create_user(
        email="worker@nlp.test",
        full_name="NLP Worker",
        password="ShiftSync@2026!",
        role=UserRole.OUTGOING_WORKER,
        organisation=org,
    )


@pytest.mark.django_db
class TestNLPServiceAndEndpoints:
    def test_representative_descriptions_classification(self, nlp_user):
        client = APIClient()
        client.force_authenticate(user=nlp_user)

        res = client.post(
            "/api/nlp/predict/",
            {
                "description": (
                    "Major safety alert: jet fuel seepage detected at engine pylon fuel "
                    "disconnect coupling; aircraft grounded pending seal swap."
                )
            },
            format="json",
        )
        assert res.status_code == 200
        assert res.data["available"] is True
        assert res.data["category"] in [
            "Safety & Compliance",
            "Maintenance",
            "Equipment Check",
            "Operations",
            "Administration",
        ]
        assert res.data["priority"] in ["Low", "Medium", "High", "Critical"]
        assert isinstance(res.data["confidence_score"], float)

    def test_malformed_or_empty_input_rejected(self, nlp_user):
        client = APIClient()
        client.force_authenticate(user=nlp_user)

        res_empty = client.post("/api/nlp/predict/", {"description": "   "}, format="json")
        assert res_empty.status_code == 400

        res_symbols = client.post("/api/nlp/predict/", {"description": "???"}, format="json")
        assert res_symbols.status_code == 400

    def test_low_confidence_flag_on_ambiguous_short_input(self, nlp_user):
        client = APIClient()
        client.force_authenticate(user=nlp_user)

        res = client.post(
            "/api/nlp/predict/",
            {"description": "check unit"},
            format="json",
        )
        assert res.status_code == 200
        assert res.data["is_low_confidence"] is True
        assert res.data["warning"] is not None

    def test_graceful_fallback_when_nlp_unavailable(self, nlp_user):
        client = APIClient()
        client.force_authenticate(user=nlp_user)

        res = client.post(
            "/api/nlp/predict/",
            {
                "description": "Replaced worn conveyor belt bearing in packaging area.",
                "provider": "unavailable",
            },
            format="json",
        )
        assert res.status_code == 200
        assert res.data["available"] is False
        assert res.data["provider"] == "manual_fallback"
        assert res.data["warning"] is not None

    def test_multi_task_shift_log_segmentation(self, nlp_user):
        client = APIClient()
        client.force_authenticate(user=nlp_user)

        res = client.post(
            "/api/nlp/analyze-log/",
            {
                "shift_notes": (
                    "Checked Boeing 787 left engine oil pressure sensor readings, "
                    "and replaced faulty VHF Comm #1 transceiver LRU, "
                    "and archived TechLog page #4412."
                )
            },
            format="json",
        )
        assert res.status_code == 200
        assert res.data["tasks_detected_count"] >= 2
        assert len(res.data["tasks"]) >= 2
