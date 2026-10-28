from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckAPIView(APIView):
    """
    GET /api/health/
    Lightweight liveness/readiness probe for load balancers, CI and monitoring.
    Verifies database connectivity only; it does not load the NLP model, and it
    exposes no operational data, so it is safe to leave unauthenticated.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(responses={200: dict, 503: dict})
    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            db_ok = False

        payload = {
            "status": "ok" if db_ok else "degraded",
            "database": "up" if db_ok else "down",
            "timestamp": timezone.now().isoformat(),
        }
        return Response(
            payload,
            status=status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
