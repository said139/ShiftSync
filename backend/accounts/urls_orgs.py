from django.urls import path
from .views import AuditEventListAPIView, CurrentOrganisationConfigAPIView

urlpatterns = [
    path("current/", CurrentOrganisationConfigAPIView.as_view(), name="org-current"),
    path("audit-logs/", AuditEventListAPIView.as_view(), name="org-audit-logs"),
]
