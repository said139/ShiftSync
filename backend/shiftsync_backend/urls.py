from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .health import HealthCheckAPIView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # Liveness / readiness probe
    path("api/health/", HealthCheckAPIView.as_view(), name="health"),
    # OpenAPI Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # Core Application REST API Endpoints
    path("api/auth/", include("accounts.urls_auth")),
    path("api/users/", include("accounts.urls_users")),
    path("api/organisations/", include("accounts.urls_orgs")),
    path("api/", include("operations.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/nlp/", include("nlp_service.urls")),
]
