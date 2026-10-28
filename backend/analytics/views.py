import csv
from collections import defaultdict
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from accounts.permissions import IsSupervisorOrAdmin
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from operations.models import (
    EquipmentStatusChoice,
    HandoverReport,
    HandoverStatus,
    Shift,
    ShiftStatus,
    Task,
    TaskPriority,
    TaskStatus,
)
from operations.serializers import (
    HandoverReportSerializer,
    ShiftSerializer,
    TaskSerializer,
)


def apply_date_filters(shifts_qs, handovers_qs, tasks_qs, date_from, date_to):
    if date_from:
        shifts_qs = shifts_qs.filter(shift_date__gte=date_from)
        handovers_qs = handovers_qs.filter(shift__shift_date__gte=date_from)
        tasks_qs = tasks_qs.filter(shift__shift_date__gte=date_from)
    if date_to:
        shifts_qs = shifts_qs.filter(shift_date__lte=date_to)
        handovers_qs = handovers_qs.filter(shift__shift_date__lte=date_to)
        tasks_qs = tasks_qs.filter(shift__shift_date__lte=date_to)
    return shifts_qs, handovers_qs, tasks_qs


class DashboardSummaryAPIView(APIView):
    """
    GET /api/analytics/dashboard/
    Computes live operational dashboard metrics from PostgreSQL records.
    Adapts scope based on role (Worker personal + shift context vs Supervisor/Admin org-wide scope),
    or explicit `scope=personal|organisation` query parameter.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        org = user.organisation
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        requested_scope = request.query_params.get("scope", "auto")

        is_supervisory = user.role in (UserRole.SUPERVISOR, UserRole.ADMIN)
        use_org_scope = is_supervisory if requested_scope == "auto" else (requested_scope == "organisation")

        shifts_qs = Shift.objects.select_related(
            "outgoing_worker", "incoming_worker", "supervisor"
        ).filter(organisation=org)

        handovers_qs = (
            HandoverReport.objects.select_related(
                "shift",
                "submitting_worker",
                "designated_incoming_worker",
                "acknowledged_by",
            )
            .prefetch_related("tasks")
            .filter(organisation=org)
        )

        tasks_qs = Task.objects.select_related(
            "shift", "handover_report", "created_by", "assignee"
        ).filter(organisation=org)

        if not use_org_scope:
            shifts_qs = shifts_qs.filter(
                Q(outgoing_worker=user) | Q(incoming_worker=user)
            )
            handovers_qs = handovers_qs.filter(
                Q(submitting_worker=user) | Q(designated_incoming_worker=user)
            )
            tasks_qs = tasks_qs.filter(
                Q(created_by=user)
                | Q(assignee=user)
                | Q(shift__outgoing_worker=user)
                | Q(shift__incoming_worker=user)
            ).distinct()
            if user.role == UserRole.INCOMING_WORKER:
                handovers_qs = handovers_qs.exclude(
                    Q(status=HandoverStatus.DRAFT) & ~Q(submitting_worker=user)
                )

        shifts_qs, handovers_qs, tasks_qs = apply_date_filters(
            shifts_qs, handovers_qs, tasks_qs, date_from, date_to
        )

        # Metric Calculations with explicit numerators and denominators
        active_shifts_count = shifts_qs.filter(status=ShiftStatus.ACTIVE).count()
        scheduled_shifts_count = shifts_qs.filter(status=ShiftStatus.SCHEDULED).count()
        total_shifts_count = shifts_qs.exclude(status=ShiftStatus.CANCELLED).count()

        draft_handovers_count = handovers_qs.filter(status=HandoverStatus.DRAFT).count()
        awaiting_ack_count = handovers_qs.filter(
            status=HandoverStatus.SUBMITTED
        ).count()
        acknowledged_count = handovers_qs.filter(
            status=HandoverStatus.ACKNOWLEDGED
        ).count()
        total_submitted_count = awaiting_ack_count + acknowledged_count

        unresolved_tasks_qs = tasks_qs.exclude(status=TaskStatus.COMPLETED)
        unresolved_tasks_count = unresolved_tasks_qs.count()
        carried_forward_count = unresolved_tasks_qs.filter(
            is_carried_forward=True
        ).count()
        critical_unresolved_count = unresolved_tasks_qs.filter(
            priority=TaskPriority.CRITICAL
        ).count()
        completed_tasks_count = tasks_qs.filter(status=TaskStatus.COMPLETED).count()
        total_tasks_count = tasks_qs.count()

        # Handover completion rate: % of submitted handovers that have been formally acknowledged
        if total_submitted_count > 0:
            completion_rate = round(
                (acknowledged_count / total_submitted_count) * 100.0, 1
            )
        else:
            completion_rate = 0.0

        # Time-series chart data by shift_date
        trend_map = defaultdict(
            lambda: {"date": "", "submitted": 0, "acknowledged": 0, "draft": 0}
        )
        for h in handovers_qs:
            d_str = str(h.shift.shift_date)
            trend_map[d_str]["date"] = d_str
            if h.status == HandoverStatus.DRAFT:
                trend_map[d_str]["draft"] += 1
            elif h.status == HandoverStatus.SUBMITTED:
                trend_map[d_str]["submitted"] += 1
            elif h.status == HandoverStatus.ACKNOWLEDGED:
                trend_map[d_str]["submitted"] += 1
                trend_map[d_str]["acknowledged"] += 1

        completion_trend = []
        for d_key in sorted(trend_map.keys()):
            item = trend_map[d_key]
            sub = item["submitted"]
            ack = item["acknowledged"]
            rate = round((ack / sub) * 100.0, 1) if sub > 0 else 0.0
            completion_trend.append(
                {
                    "date": d_key,
                    "submitted": sub,
                    "acknowledged": ack,
                    "draft": item["draft"],
                    "completion_rate": rate,
                }
            )

        # Critical issues list (critical unresolved tasks + safety/equipment alerts)
        critical_tasks_list = TaskSerializer(
            unresolved_tasks_qs.filter(priority=TaskPriority.CRITICAL)[:10],
            many=True,
        ).data

        safety_and_equipment_alerts = []
        for h in handovers_qs.filter(
            Q(has_safety_incident=True)
            | ~Q(safety_issues="")
            | Q(
                equipment_status__in=[
                    EquipmentStatusChoice.MAINTENANCE_REQUIRED,
                    EquipmentStatusChoice.CRITICAL_FAULT,
                ]
            )
        )[:8]:
            safety_and_equipment_alerts.append(
                {
                    "handover_id": str(h.id),
                    "report_code": h.report_code,
                    "shift_name": h.shift.name,
                    "shift_date": str(h.shift.shift_date),
                    "equipment_status": h.equipment_status,
                    "equipment_status_display": h.get_equipment_status_display(),
                    "safety_issues": h.safety_issues,
                    "status": h.status,
                    "submitting_worker_name": h.submitting_worker.full_name,
                }
            )

        recent_notifications = NotificationSerializer(
            Notification.objects.filter(recipient=user, organisation=org)[:8],
            many=True,
        ).data

        return Response(
            {
                "scope": "organisation" if use_org_scope else "personal",
                "role": user.role,
                "organisation_name": org.name,
                "filters_applied": {
                    "date_from": date_from,
                    "date_to": date_to,
                },
                "metrics": {
                    "active_shifts": active_shifts_count,
                    "scheduled_shifts": scheduled_shifts_count,
                    "total_shifts": total_shifts_count,
                    "handovers_awaiting_acknowledgment": awaiting_ack_count,
                    "submitted_handovers": total_submitted_count,
                    "acknowledged_handovers": acknowledged_count,
                    "draft_handovers": draft_handovers_count,
                    "unresolved_tasks": unresolved_tasks_count,
                    "carried_forward_tasks": carried_forward_count,
                    "critical_priority_tasks": critical_unresolved_count,
                    "completed_tasks": completed_tasks_count,
                    "total_tasks": total_tasks_count,
                    "handover_completion_rate": completion_rate,
                    "completion_rate_numerator": acknowledged_count,
                    "completion_rate_denominator": total_submitted_count,
                },
                "recent_handovers": HandoverReportSerializer(
                    handovers_qs[:8], many=True, context={"request": request}
                ).data,
                "outstanding_tasks": TaskSerializer(
                    unresolved_tasks_qs[:10], many=True
                ).data,
                "critical_tasks": critical_tasks_list,
                "safety_and_equipment_alerts": safety_and_equipment_alerts,
                "upcoming_and_active_shifts": ShiftSerializer(
                    shifts_qs.filter(
                        status__in=[ShiftStatus.ACTIVE, ShiftStatus.SCHEDULED]
                    )[:8],
                    many=True,
                ).data,
                "recent_notifications": recent_notifications,
                "completion_trend": completion_trend,
            }
        )


class SupervisorAnalyticsAPIView(APIView):
    """
    GET /api/analytics/supervisor-report/
    Detailed supervisory analytics: category breakdown, priority breakdown,
    worker handover performance, acknowledgment latency, and NLP accuracy/override stats.
    """

    permission_classes = [IsSupervisorOrAdmin]

    def get(self, request):
        org = request.user.organisation
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        status_filter = request.query_params.get("status")
        worker_filter = request.query_params.get("worker")
        priority_filter = request.query_params.get("priority")
        shift_filter = request.query_params.get("shift")

        shifts_qs = Shift.objects.filter(organisation=org)
        handovers_qs = HandoverReport.objects.select_related(
            "shift",
            "submitting_worker",
            "designated_incoming_worker",
            "acknowledged_by",
        ).filter(organisation=org)
        tasks_qs = Task.objects.select_related("shift", "handover_report").filter(
            organisation=org
        )

        shifts_qs, handovers_qs, tasks_qs = apply_date_filters(
            shifts_qs, handovers_qs, tasks_qs, date_from, date_to
        )

        if status_filter:
            handovers_qs = handovers_qs.filter(status=status_filter)
        if shift_filter:
            handovers_qs = handovers_qs.filter(shift_id=shift_filter)
            tasks_qs = tasks_qs.filter(shift_id=shift_filter)
        if worker_filter:
            handovers_qs = handovers_qs.filter(
                Q(submitting_worker_id=worker_filter)
                | Q(designated_incoming_worker_id=worker_filter)
            )
            tasks_qs = tasks_qs.filter(
                Q(created_by_id=worker_filter) | Q(assignee_id=worker_filter)
            )
        if priority_filter:
            tasks_qs = tasks_qs.filter(priority=priority_filter)

        # Category Breakdown
        cat_rows = (
            tasks_qs.values("category")
            .annotate(
                total=Count("id"),
                completed=Count("id", filter=Q(status=TaskStatus.COMPLETED)),
                unresolved=Count("id", filter=~Q(status=TaskStatus.COMPLETED)),
                critical=Count("id", filter=Q(priority=TaskPriority.CRITICAL)),
            )
            .order_by("-total")
        )

        # Priority Breakdown
        prio_rows = (
            tasks_qs.values("priority")
            .annotate(
                total=Count("id"),
                completed=Count("id", filter=Q(status=TaskStatus.COMPLETED)),
                unresolved=Count("id", filter=~Q(status=TaskStatus.COMPLETED)),
            )
            .order_by("-total")
        )

        # NLP Suggestion vs Override Statistics
        nlp_classified_qs = tasks_qs.exclude(model_suggested_category="")
        nlp_total = nlp_classified_qs.count()
        nlp_overridden = nlp_classified_qs.filter(was_overridden=True).count()
        nlp_accepted = nlp_total - nlp_overridden
        nlp_acceptance_rate = (
            round((nlp_accepted / nlp_total) * 100.0, 1) if nlp_total > 0 else 100.0
        )

        # Average Acknowledgment Turnaround Time (minutes)
        ack_handovers = handovers_qs.filter(
            status=HandoverStatus.ACKNOWLEDGED,
            submitted_at__isnull=False,
            acknowledged_at__isnull=False,
        )
        turnaround_minutes = []
        for h in ack_handovers:
            delta_mins = (h.acknowledged_at - h.submitted_at).total_seconds() / 60.0
            if delta_mins >= 0:
                turnaround_minutes.append(delta_mins)
        avg_ack_minutes = (
            round(sum(turnaround_minutes) / len(turnaround_minutes), 1)
            if turnaround_minutes
            else 0.0
        )

        return Response(
            {
                "organisation": org.name,
                "total_handovers": handovers_qs.count(),
                "submitted_count": handovers_qs.filter(
                    status=HandoverStatus.SUBMITTED
                ).count(),
                "acknowledged_count": handovers_qs.filter(
                    status=HandoverStatus.ACKNOWLEDGED
                ).count(),
                "draft_count": handovers_qs.filter(status=HandoverStatus.DRAFT).count(),
                "average_acknowledgment_minutes": avg_ack_minutes,
                "category_breakdown": list(cat_rows),
                "priority_breakdown": list(prio_rows),
                "nlp_statistics": {
                    "total_nlp_assisted_tasks": nlp_total,
                    "accepted_without_override": nlp_accepted,
                    "manually_overridden": nlp_overridden,
                    "acceptance_rate_percent": nlp_acceptance_rate,
                },
                "handovers": HandoverReportSerializer(
                    handovers_qs[:50], many=True, context={"request": request}
                ).data,
            }
        )


class ExportHandoverCSVAPIView(APIView):
    """
    GET /api/analytics/export-csv/
    Exports filtered handover performance records as a downloadable CSV report for Supervisors and Admins.
    """

    permission_classes = [IsSupervisorOrAdmin]

    def get(self, request):
        org = request.user.organisation
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        status_filter = request.query_params.get("status")

        handovers_qs = (
            HandoverReport.objects.select_related(
                "shift",
                "submitting_worker",
                "designated_incoming_worker",
                "acknowledged_by",
            )
            .prefetch_related("tasks")
            .filter(organisation=org)
        )
        if date_from:
            handovers_qs = handovers_qs.filter(shift__shift_date__gte=date_from)
        if date_to:
            handovers_qs = handovers_qs.filter(shift__shift_date__lte=date_to)
        if status_filter:
            handovers_qs = handovers_qs.filter(status=status_filter)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="shiftsync_handover_report_{timestamp}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(
            [
                "Report Code",
                "Shift Name",
                "Shift Date",
                "Department",
                "Outgoing Worker",
                "Designated Incoming Worker",
                "Status",
                "Equipment Status",
                "Total Tasks",
                "Unresolved Tasks",
                "Critical Tasks",
                "Safety Issues",
                "Submitted At (UTC)",
                "Acknowledged By",
                "Acknowledged At (UTC)",
            ]
        )

        for h in handovers_qs:
            total_t = h.tasks.count()
            unresolved_t = h.tasks.exclude(status=TaskStatus.COMPLETED).count()
            critical_t = h.tasks.filter(priority=TaskPriority.CRITICAL).count()
            writer.writerow(
                [
                    h.report_code,
                    h.shift.name,
                    str(h.shift.shift_date),
                    h.shift.department,
                    h.submitting_worker.full_name,
                    h.designated_incoming_worker.full_name,
                    h.status,
                    h.get_equipment_status_display(),
                    total_t,
                    unresolved_t,
                    critical_t,
                    h.safety_issues or "None",
                    h.submitted_at.isoformat() if h.submitted_at else "",
                    h.acknowledged_by.full_name if h.acknowledged_by else "",
                    h.acknowledged_at.isoformat() if h.acknowledged_at else "",
                ]
            )

        return response
