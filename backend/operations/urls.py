from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    AcknowledgmentEventViewSet,
    HandoverReportViewSet,
    ShiftViewSet,
    TaskViewSet,
)

router = DefaultRouter()
router.register(r"shifts", ShiftViewSet, basename="shifts")
router.register(r"handovers", HandoverReportViewSet, basename="handovers")
router.register(r"tasks", TaskViewSet, basename="tasks")
router.register(r"acknowledgments", AcknowledgmentEventViewSet, basename="acknowledgments")

urlpatterns = [
    path("", include(router.urls)),
]
