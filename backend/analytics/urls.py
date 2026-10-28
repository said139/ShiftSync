from django.urls import path
from .views import (
    DashboardSummaryAPIView,
    ExportHandoverCSVAPIView,
    SupervisorAnalyticsAPIView,
)

urlpatterns = [
    path("dashboard/", DashboardSummaryAPIView.as_view(), name="analytics-dashboard"),
    path(
        "supervisor-report/",
        SupervisorAnalyticsAPIView.as_view(),
        name="analytics-supervisor-report",
    ),
    path(
        "export-csv/",
        ExportHandoverCSVAPIView.as_view(),
        name="analytics-export-csv",
    ),
]
