from django.db import models, transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.models import User, UserRole
from accounts.permissions import IsOutgoingOrAdmin, IsSystemAdmin
from accounts.views import get_client_ip, log_audit_event
from accounts.email_service import (
    send_handover_submitted_email,
    send_handover_acknowledged_email,
)
from common.ws_broadcast import push_ws_event_to_org, push_ws_event_to_user
from notifications.models import Notification, NotificationType
from .models import (
    AcknowledgmentEvent,
    HandoverAmendment,
    HandoverReport,
    HandoverStatus,
    Shift,
    ShiftStatus,
    Task,
    TaskPriority,
    TaskStatus,
    TaskStatusHistory,
)
from .serializers import (
    AcknowledgmentEventSerializer,
    HandoverAmendmentSerializer,
    HandoverReportSerializer,
    ShiftSerializer,
    TaskSerializer,
    TaskStatusHistorySerializer,
)


def notify_supervisors(organisation, notification_type, title, message, handover=None, task=None):
    supervisors = User.objects.filter(
        organisation=organisation,
        role=UserRole.SUPERVISOR,
        is_active=True,
    )
    notifications = [
        Notification(
            organisation=organisation,
            recipient=sup,
            notification_type=notification_type,
            related_handover=handover,
            related_task=task,
            title=title,
            message=message,
        )
        for sup in supervisors
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)
        for sup in supervisors:
            push_ws_event_to_user(
                sup.id,
                "NEW_NOTIFICATION",
                {
                    "title": title,
                    "message": message,
                    "type": notification_type,
                },
            )


class ShiftViewSet(viewsets.ModelViewSet):
    """
    Shift management:
    - Admins can create, update, assign workers, and manage shifts.
    - Supervisors and Workers can view shifts in their organisation and filter by date/status/assignment.
    """

    serializer_class = ShiftSerializer
    filterset_fields = [
        "status",
        "shift_date",
        "department",
        "outgoing_worker",
        "incoming_worker",
    ]
    search_fields = [
        "name",
        "department",
        "outgoing_worker__full_name",
        "incoming_worker__full_name",
    ]
    ordering_fields = ["shift_date", "start_time", "created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Shift.objects.select_related(
            "organisation", "outgoing_worker", "incoming_worker", "supervisor"
        ).filter(organisation=user.organisation)

        my_shifts = self.request.query_params.get("my_shifts")
        if my_shifts and my_shifts.lower() in ("true", "1"):
            qs = qs.filter(
                models.Q(outgoing_worker=user)
                | models.Q(incoming_worker=user)
                | models.Q(supervisor=user)
            )

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(shift_date__gte=date_from)
        if date_to:
            qs = qs.filter(shift_date__lte=date_to)

        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve", "my_active", "my_duty"):
            return [permissions.IsAuthenticated()]
        return [IsSystemAdmin()]

    def perform_create(self, serializer):
        user = self.request.user
        shift = serializer.save(organisation=user.organisation)
        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="SHIFT_CREATED",
            target_type="Shift",
            target_id=shift.id,
            summary=(
                f"Admin created shift '{shift.name}' ({shift.shift_date}) "
                f"Assigning Outgoing: {shift.outgoing_worker.full_name} -> Incoming: {shift.incoming_worker.full_name}."
            ),
            request=self.request,
        )
        for recipient, role_label in [
            (shift.outgoing_worker, "Outgoing Worker"),
            (shift.incoming_worker, "Incoming Worker"),
        ]:
            Notification.objects.create(
                organisation=user.organisation,
                recipient=recipient,
                notification_type=NotificationType.SHIFT_ASSIGNED,
                title=f"Shift Assignment: {shift.name}",
                message=(
                    f"You have been assigned as the {role_label} for shift '{shift.name}' "
                    f"on {shift.shift_date} ({shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')})."
                ),
            )

    def perform_update(self, serializer):
        user = self.request.user
        shift = serializer.save()
        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="SHIFT_UPDATED",
            target_type="Shift",
            target_id=shift.id,
            summary=f"Admin updated shift '{shift.name}' ({shift.shift_date}, status={shift.status}).",
            request=self.request,
        )

    @action(detail=False, methods=["get"], url_path="my-active")
    def my_active(self, request):
        """Returns shifts assigned to the current worker (outgoing or incoming)."""
        user = request.user
        qs = self.get_queryset().filter(
            models.Q(outgoing_worker=user) | models.Q(incoming_worker=user)
        )
        return Response(ShiftSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="my-duty")
    def my_duty(self, request):
        """
        Returns the authenticated worker's current operational shift assignment:
        indicates whether the user is currently the OUTGOING worker (preparing handover)
        or INCOMING worker (receiving & acknowledging handover) for their assigned shift(s).
        """
        user = request.user
        today = timezone.localdate()

        # 1. Look for currently ACTIVE shift where user is assigned
        active_shifts = (
            self.get_queryset()
            .filter(
                models.Q(outgoing_worker=user) | models.Q(incoming_worker=user),
                status=ShiftStatus.ACTIVE,
            )
            .select_related("outgoing_worker", "incoming_worker", "supervisor")
        )

        # 2. Or scheduled shift for today/upcoming if no active shift
        if not active_shifts.exists():
            active_shifts = (
                self.get_queryset()
                .filter(
                    models.Q(outgoing_worker=user) | models.Q(incoming_worker=user),
                    status=ShiftStatus.SCHEDULED,
                    shift_date__gte=today,
                )
                .order_by("shift_date", "start_time")
                .select_related("outgoing_worker", "incoming_worker", "supervisor")
            )

        current_shift = active_shifts.first()
        if not current_shift:
            # Check if there is any past completed shift or general assignment
            any_shift = (
                self.get_queryset()
                .filter(
                    models.Q(outgoing_worker=user) | models.Q(incoming_worker=user)
                )
                .order_by("-shift_date", "-start_time")
                .select_related("outgoing_worker", "incoming_worker", "supervisor")
                .first()
            )
            if any_shift:
                is_out = any_shift.outgoing_worker_id == user.id
                partner = any_shift.incoming_worker if is_out else any_shift.outgoing_worker
                return Response(
                    {
                        "has_assignment": True,
                        "is_active_now": False,
                        "role_type": "OUTGOING" if is_out else "INCOMING",
                        "role_label": "Outgoing Worker (Recent Duty)" if is_out else "Incoming Worker (Recent Duty)",
                        "is_outgoing": is_out,
                        "is_incoming": not is_out,
                        "shift": ShiftSerializer(any_shift).data,
                        "partner_worker": {
                            "id": str(partner.id),
                            "full_name": partner.full_name,
                            "email": partner.email,
                            "employee_id": partner.employee_id,
                            "department": partner.department,
                        } if partner else None,
                        "handover": None,
                        "suggested_action": "VIEW_SCHEDULE",
                        "suggested_action_label": "View Master Shift Schedule",
                        "suggested_url": "/shifts",
                    }
                )

            return Response(
                {
                    "has_assignment": False,
                    "is_active_now": False,
                    "role_type": "STANDBY",
                    "role_label": "Operational Standby / Off Duty",
                    "is_outgoing": False,
                    "is_incoming": False,
                    "shift": None,
                    "handover": None,
                    "partner_worker": None,
                    "suggested_action": "VIEW_SCHEDULE",
                    "suggested_action_label": "View Master Shift Schedule",
                    "suggested_url": "/shifts",
                }
            )

        is_outgoing = current_shift.outgoing_worker_id == user.id
        is_incoming = current_shift.incoming_worker_id == user.id
        partner = (
            current_shift.incoming_worker if is_outgoing else current_shift.outgoing_worker
        )

        handover = current_shift.handover_reports.order_by("-created_at").first()
        handover_data = None
        if handover:
            handover_data = {
                "id": str(handover.id),
                "report_code": handover.report_code,
                "status": handover.status,
                "status_display": handover.get_status_display(),
                "task_count": handover.tasks.count(),
                "unresolved_tasks": handover.tasks.exclude(
                    status=TaskStatus.COMPLETED
                ).count(),
                "has_safety_incident": handover.has_safety_incident,
            }

        role_type = "OUTGOING" if is_outgoing else "INCOMING"
        role_label = (
            "Outgoing Worker (Handing Over Responsibility)"
            if is_outgoing
            else "Incoming Worker (Receiving Shift & Acknowledging)"
        )

        if is_outgoing:
            if not handover:
                act = "CREATE_HANDOVER"
                act_label = "Record Tasks & Create Handover"
                act_url = "/handovers/create"
            elif handover.status == HandoverStatus.DRAFT:
                act = "EDIT_DRAFT"
                act_label = f"Continue Handover Draft ({handover.report_code})"
                act_url = f"/handovers/{handover.id}/edit"
            else:
                act = "VIEW_SUBMITTED"
                act_label = f"View Handover Report ({handover.report_code})"
                act_url = f"/handovers/{handover.id}"
        else:
            if handover and handover.status == HandoverStatus.SUBMITTED:
                act = "ACKNOWLEDGE"
                act_label = f"Review & Acknowledge Handover ({handover.report_code})"
                act_url = f"/handovers/{handover.id}/acknowledge"
            elif handover and handover.status == HandoverStatus.ACKNOWLEDGED:
                act = "VIEW_ACKNOWLEDGED"
                act_label = f"View Acknowledged Handover ({handover.report_code})"
                act_url = f"/handovers/{handover.id}"
            else:
                act = "AWAITING_SUBMISSION"
                act_label = "Awaiting Handover from Outgoing Crew"
                act_url = "/handovers/incoming"

        return Response(
            {
                "has_assignment": True,
                "is_active_now": current_shift.status == ShiftStatus.ACTIVE,
                "role_type": role_type,
                "role_label": role_label,
                "is_outgoing": is_outgoing,
                "is_incoming": is_incoming,
                "shift": ShiftSerializer(current_shift).data,
                "partner_worker": {
                    "id": str(partner.id),
                    "full_name": partner.full_name,
                    "email": partner.email,
                    "employee_id": partner.employee_id,
                    "department": partner.department,
                }
                if partner
                else None,
                "handover": handover_data,
                "suggested_action": act,
                "suggested_action_label": act_label,
                "suggested_url": act_url,
            }
        )


class HandoverReportViewSet(viewsets.ModelViewSet):
    """
    Complete handover lifecycle management:
    - Create draft, edit draft, submit formally, review & acknowledge explicitly, and auditable amendments.
    """

    serializer_class = HandoverReportSerializer
    filterset_fields = [
        "status",
        "shift",
        "submitting_worker",
        "designated_incoming_worker",
        "equipment_status",
        "has_safety_incident",
    ]
    search_fields = [
        "report_code",
        "shift__name",
        "submitting_worker__full_name",
        "designated_incoming_worker__full_name",
        "safety_issues",
        "additional_notes",
    ]
    ordering_fields = ["created_at", "submitted_at", "acknowledged_at"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            HandoverReport.objects.select_related(
                "organisation",
                "shift",
                "shift__outgoing_worker",
                "shift__incoming_worker",
                "submitting_worker",
                "designated_incoming_worker",
                "acknowledged_by",
            )
            .prefetch_related(
                "tasks",
                "tasks__history",
                "tasks__created_by",
                "tasks__assignee",
                "acknowledgment_events",
                "amendments",
            )
            .filter(organisation=user.organisation)
        )

        # Role-based visibility rules:
        # Incoming workers do not see someone else's unsent DRAFT reports
        if user.role == UserRole.INCOMING_WORKER:
            qs = qs.exclude(
                models.Q(status=HandoverStatus.DRAFT) & ~models.Q(submitting_worker=user)
            )

        scope = self.request.query_params.get("scope")
        if scope == "assigned_to_me":
            qs = qs.filter(designated_incoming_worker=user).exclude(
                status=HandoverStatus.DRAFT
            )
        elif scope == "submitted_by_me":
            qs = qs.filter(submitting_worker=user)
        elif scope == "pending_acknowledgment":
            qs = qs.filter(status=HandoverStatus.SUBMITTED)

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(shift__shift_date__gte=date_from)
        if date_to:
            qs = qs.filter(shift__shift_date__lte=date_to)

        priority = self.request.query_params.get("priority")
        if priority:
            qs = qs.filter(tasks__priority=priority).distinct()

        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsOutgoingOrAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        report = serializer.save()
        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="HANDOVER_DRAFT_CREATED",
            target_type="HandoverReport",
            target_id=report.id,
            summary=f"{user.full_name} created handover draft {report.report_code} for shift '{report.shift.name}'.",
            request=self.request,
        )

    def perform_update(self, serializer):
        report = self.get_object()
        user = self.request.user
        if report.status != HandoverStatus.DRAFT:
            raise ValidationError(
                {"detail": "Only Draft handover reports can be edited. Submitted reports are locked."}
            )
        if report.submitting_worker_id != user.id and user.role != UserRole.ADMIN:
            raise PermissionDenied(
                "Only the authoring outgoing worker or a System Administrator can edit this draft."
            )
        updated = serializer.save()
        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="HANDOVER_DRAFT_UPDATED",
            target_type="HandoverReport",
            target_id=updated.id,
            summary=f"{user.full_name} updated handover draft {updated.report_code}.",
            request=self.request,
        )

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.status != HandoverStatus.DRAFT:
            raise ValidationError(
                {"detail": "Submitted or acknowledged handover reports cannot be deleted."}
            )
        if instance.submitting_worker_id != user.id and user.role != UserRole.ADMIN:
            raise PermissionDenied("You do not have permission to delete this draft.")
        code = instance.report_code
        instance.delete()
        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="HANDOVER_DRAFT_DELETED",
            target_type="HandoverReport",
            target_id=code,
            summary=f"{user.full_name} deleted draft handover report {code}.",
            request=self.request,
        )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        """
        Step 5: Formally submits a Draft handover report inside an atomic transaction.
        Prevents duplicate submissions, locks ordinary editing, and notifies incoming worker & supervisors.
        """
        report = self.get_object()
        user = request.user

        if report.submitting_worker_id != user.id and user.role != UserRole.ADMIN:
            raise PermissionDenied(
                "Only the assigned outgoing worker or a System Administrator may submit this handover report."
            )

        if report.status != HandoverStatus.DRAFT:
            return Response(
                {
                    "detail": f"Handover {report.report_code} has already been submitted (current status: {report.status}). Duplicate submission prevented."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Allow optional final tasks_input or fields in the submit request payload
        if any(
            k in request.data
            for k in (
                "tasks_input",
                "equipment_status",
                "safety_issues",
                "additional_notes",
                "designated_incoming_worker",
            )
        ):
            serializer = self.get_serializer(report, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            report = serializer.save()

        task_count = report.tasks.count()
        if task_count == 0:
            return Response(
                {
                    "detail": "Cannot submit an empty handover report. Please record at least one shift task before submitting."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            now = timezone.now()
            report.status = HandoverStatus.SUBMITTED
            report.submitted_at = now
            report.save(update_fields=["status", "submitted_at", "updated_at"])

            # Assign any unassigned pending/in-progress tasks to the designated incoming worker
            report.tasks.exclude(status=TaskStatus.COMPLETED).filter(
                assignee__isnull=True
            ).update(assignee=report.designated_incoming_worker)

            critical_tasks = report.tasks.filter(priority=TaskPriority.CRITICAL)
            unresolved_count = report.tasks.exclude(
                status=TaskStatus.COMPLETED
            ).count()

            # Notify Designated Incoming Worker
            Notification.objects.create(
                organisation=report.organisation,
                recipient=report.designated_incoming_worker,
                notification_type=NotificationType.HANDOVER_SUBMITTED,
                related_handover=report,
                title=f"Handover Awaiting Acknowledgment: {report.report_code}",
                message=(
                    f"{report.submitting_worker.full_name} submitted handover report {report.report_code} "
                    f"for shift '{report.shift.name}' with {task_count} task(s) ({unresolved_count} unresolved). "
                    f"Please review and formally acknowledge receipt."
                ),
            )

            # Notify Supervisors
            notify_supervisors(
                organisation=report.organisation,
                notification_type=NotificationType.HANDOVER_SUBMITTED,
                title=f"Handover Submitted: {report.report_code}",
                message=(
                    f"{report.submitting_worker.full_name} submitted {report.report_code} to "
                    f"{report.designated_incoming_worker.full_name} ({task_count} tasks, "
                    f"{critical_tasks.count()} critical)."
                ),
                handover=report,
            )

            # Create dedicated critical alert if critical tasks or safety incident exist
            if critical_tasks.exists() or report.has_safety_incident:
                crit_msg = (
                    f"Handover {report.report_code} contains {critical_tasks.count()} Critical-priority task(s)"
                    + (
                        f" and a reported safety issue: {report.safety_issues[:120]}"
                        if report.safety_issues
                        else "."
                    )
                )
                Notification.objects.create(
                    organisation=report.organisation,
                    recipient=report.designated_incoming_worker,
                    notification_type=NotificationType.CRITICAL_TASK,
                    related_handover=report,
                    title=f"CRITICAL ALERT in {report.report_code}",
                    message=crit_msg,
                )
                notify_supervisors(
                    organisation=report.organisation,
                    notification_type=NotificationType.CRITICAL_TASK,
                    title=f"Critical Operational Alert: {report.report_code}",
                    message=crit_msg,
                    handover=report,
                )

            log_audit_event(
                organisation=report.organisation,
                actor=user,
                action="HANDOVER_SUBMITTED",
                target_type="HandoverReport",
                target_id=report.id,
                summary=(
                    f"{user.full_name} formally submitted handover {report.report_code} "
                    f"to {report.designated_incoming_worker.full_name} ({task_count} tasks)."
                ),
                metadata={
                    "report_code": report.report_code,
                    "task_count": task_count,
                    "unresolved_count": unresolved_count,
                    "critical_count": critical_tasks.count(),
                },
                request=request,
            )

        report.refresh_from_db()

        # Broadcast real-time WS events
        push_ws_event_to_user(
            report.designated_incoming_worker_id,
            "HANDOVER_SUBMITTED",
            {
                "report_id": str(report.id),
                "report_code": report.report_code,
                "shift_name": report.shift.name,
                "submitting_worker": report.submitting_worker.full_name,
                "task_count": task_count,
                "has_safety_incident": report.has_safety_incident,
            },
        )
        push_ws_event_to_org(
            report.organisation_id,
            "DASHBOARD_METRIC_UPDATE",
            {
                "event": "HANDOVER_SUBMITTED",
                "report_code": report.report_code,
            },
        )

        # Dispatch real SMTP notification email to incoming crew member
        send_handover_submitted_email(report)

        return Response(
            HandoverReportSerializer(report, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        """
        Step 6: Explicit acknowledgment by the designated incoming worker (or Admin).
        Preserves unfinished tasks as carried-forward work rather than marking them completed.
        """
        report = self.get_object()
        user = request.user

        if (
            report.designated_incoming_worker_id != user.id
            and user.role != UserRole.ADMIN
        ):
            raise PermissionDenied(
                "Only the designated incoming worker assigned to this handover report may formally acknowledge it."
            )

        if report.status == HandoverStatus.DRAFT:
            return Response(
                {
                    "detail": "Draft handover reports cannot be acknowledged before formal submission."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if report.status == HandoverStatus.ACKNOWLEDGED:
            return Response(
                {
                    "detail": f"Handover {report.report_code} was already acknowledged at {report.acknowledged_at}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ack_notes = (request.data.get("acknowledgment_notes") or "").strip()
        if (
            report.organisation.require_acknowledgment_notes
            and not ack_notes
        ):
            return Response(
                {
                    "acknowledgment_notes": [
                        "Your organisation requires acknowledgment notes when signing off a handover."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            now = timezone.now()
            report.status = HandoverStatus.ACKNOWLEDGED
            report.acknowledged_by = user
            report.acknowledged_at = now
            report.acknowledgment_notes = ack_notes
            report.save(
                update_fields=[
                    "status",
                    "acknowledged_by",
                    "acknowledged_at",
                    "acknowledgment_notes",
                    "updated_at",
                ]
            )

            unresolved_tasks = list(
                report.tasks.exclude(status=TaskStatus.COMPLETED)
            )
            critical_count = report.tasks.filter(
                priority=TaskPriority.CRITICAL
            ).count()

            # Carry forward unfinished tasks into the incoming worker's active queue without marking them completed
            for u_task in unresolved_tasks:
                u_task.is_carried_forward = True
                if not u_task.assignee_id:
                    u_task.assignee = user
                u_task.save(
                    update_fields=["is_carried_forward", "assignee", "updated_at"]
                )
                TaskStatusHistory.objects.create(
                    task=u_task,
                    changed_by=user,
                    previous_status=u_task.status,
                    new_status=u_task.status,
                    previous_priority=u_task.priority,
                    new_priority=u_task.priority,
                    comment=(
                        f"Handover {report.report_code} acknowledged by {user.full_name}. "
                        f"Task carried forward into incoming shift ({u_task.status})."
                    ),
                )

            AcknowledgmentEvent.objects.create(
                organisation=report.organisation,
                handover_report=report,
                acknowledged_by=user,
                acknowledgment_notes=ack_notes,
                unresolved_tasks_count=len(unresolved_tasks),
                critical_tasks_count=critical_count,
                ip_address=get_client_ip(request),
            )

            # Notify Outgoing Worker
            Notification.objects.create(
                organisation=report.organisation,
                recipient=report.submitting_worker,
                notification_type=NotificationType.HANDOVER_ACKNOWLEDGED,
                related_handover=report,
                title=f"Handover Acknowledged: {report.report_code}",
                message=(
                    f"{user.full_name} formally acknowledged receipt of your handover report "
                    f"{report.report_code} at {now.strftime('%Y-%m-%d %H:%M UTC')}."
                    + (f" Note: '{ack_notes}'" if ack_notes else "")
                ),
            )

            # Notify Supervisors
            notify_supervisors(
                organisation=report.organisation,
                notification_type=NotificationType.HANDOVER_ACKNOWLEDGED,
                title=f"Handover Acknowledged: {report.report_code}",
                message=(
                    f"{user.full_name} acknowledged {report.report_code} from "
                    f"{report.submitting_worker.full_name}. {len(unresolved_tasks)} unresolved task(s) carried forward."
                ),
                handover=report,
            )

            log_audit_event(
                organisation=report.organisation,
                actor=user,
                action="HANDOVER_ACKNOWLEDGED",
                target_type="HandoverReport",
                target_id=report.id,
                summary=(
                    f"{user.full_name} formally acknowledged handover {report.report_code}. "
                    f"{len(unresolved_tasks)} unfinished task(s) carried forward."
                ),
                metadata={
                    "report_code": report.report_code,
                    "acknowledged_at": now.isoformat(),
                    "unresolved_tasks_carried_forward": len(unresolved_tasks),
                },
                request=request,
            )

        report.refresh_from_db()

        # Broadcast real-time WS events
        push_ws_event_to_user(
            report.submitting_worker_id,
            "HANDOVER_ACKNOWLEDGED",
            {
                "report_id": str(report.id),
                "report_code": report.report_code,
                "shift_name": report.shift.name,
                "acknowledged_by": user.full_name,
                "acknowledged_at": report.acknowledged_at.isoformat() if report.acknowledged_at else None,
            },
        )
        push_ws_event_to_org(
            report.organisation_id,
            "DASHBOARD_METRIC_UPDATE",
            {
                "event": "HANDOVER_ACKNOWLEDGED",
                "report_code": report.report_code,
            },
        )

        # Dispatch real SMTP notification email to outgoing crew member
        send_handover_acknowledged_email(report)

        return Response(
            HandoverReportSerializer(report, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="amend")
    def amend(self, request, pk=None):
        """
        Authorised, auditable amendment workflow for submitted/acknowledged reports.
        Never overwrites original submission history; appends an immutable amendment record.
        """
        report = self.get_object()
        user = request.user

        if report.status == HandoverStatus.DRAFT:
            return Response(
                {"detail": "Draft reports can be edited directly without an amendment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            report.submitting_worker_id != user.id
            and user.role not in (UserRole.ADMIN, UserRole.SUPERVISOR)
        ):
            raise PermissionDenied(
                "Only the submitting worker, a Supervisor, or an Administrator may record an amendment."
            )

        serializer = HandoverAmendmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            amendment = serializer.save(handover_report=report, author=user)
            if amendment.updated_equipment_status:
                report.equipment_status = amendment.updated_equipment_status
                report.save(update_fields=["equipment_status", "updated_at"])

            Notification.objects.create(
                organisation=report.organisation,
                recipient=report.designated_incoming_worker,
                notification_type=NotificationType.HANDOVER_AMENDED,
                related_handover=report,
                title=f"Handover Amendment Added: {report.report_code}",
                message=(
                    f"{user.full_name} recorded an official amendment on {report.report_code}: "
                    f"{amendment.amendment_reason} — {amendment.amendment_details}"
                ),
            )

            log_audit_event(
                organisation=report.organisation,
                actor=user,
                action="HANDOVER_AMENDED",
                target_type="HandoverReport",
                target_id=report.id,
                summary=f"{user.full_name} added amendment to {report.report_code}: {amendment.amendment_reason}",
                request=request,
            )

        report.refresh_from_db()
        return Response(
            HandoverReportSerializer(report, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class TaskViewSet(viewsets.ModelViewSet):
    """
    Task logging, status tracking, carry-forward visibility, and task history inspection.
    """

    serializer_class = TaskSerializer
    filterset_fields = [
        "status",
        "priority",
        "category",
        "shift",
        "handover_report",
        "assignee",
        "created_by",
        "is_carried_forward",
        "was_overridden",
    ]
    search_fields = ["description", "contextual_notes", "category"]
    ordering_fields = ["created_at", "updated_at", "due_date", "priority"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Task.objects.select_related(
                "organisation",
                "shift",
                "handover_report",
                "created_by",
                "assignee",
            )
            .prefetch_related("history", "history__changed_by")
            .filter(organisation=user.organisation)
        )

        unresolved_only = self.request.query_params.get("unresolved_only")
        if unresolved_only and unresolved_only.lower() in ("true", "1"):
            qs = qs.exclude(status=TaskStatus.COMPLETED)

        carried_forward = self.request.query_params.get("carried_forward")
        if carried_forward and carried_forward.lower() in ("true", "1"):
            qs = qs.filter(is_carried_forward=True)

        assigned_to_me = self.request.query_params.get("assigned_to_me")
        if assigned_to_me and assigned_to_me.lower() in ("true", "1"):
            qs = qs.filter(
                models.Q(assignee=user)
                | models.Q(handover_report__designated_incoming_worker=user)
            )

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(shift__shift_date__gte=date_from)
        if date_to:
            qs = qs.filter(shift__shift_date__lte=date_to)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        shift = serializer.validated_data.get("shift")
        if shift.organisation_id != user.organisation_id:
            raise PermissionDenied("Cannot log a task on another organisation's shift.")

        handover = serializer.validated_data.get("handover_report")
        if handover and handover.status != HandoverStatus.DRAFT:
            raise ValidationError(
                {"handover_report": "Cannot attach new tasks directly to a locked handover report."}
            )

        task = serializer.save(
            organisation=user.organisation,
            created_by=user,
        )
        TaskStatusHistory.objects.create(
            task=task,
            changed_by=user,
            previous_status="",
            new_status=task.status,
            previous_priority="",
            new_priority=task.priority,
            comment="Task logged.",
        )

        if task.priority == TaskPriority.CRITICAL and task.status != TaskStatus.COMPLETED:
            notify_supervisors(
                organisation=user.organisation,
                notification_type=NotificationType.CRITICAL_TASK,
                title=f"Critical Task Logged ({task.category})",
                message=f"{user.full_name} logged a Critical task on '{shift.name}': {task.description[:140]}",
                handover=task.handover_report,
                task=task,
            )

        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="TASK_CREATED",
            target_type="Task",
            target_id=task.id,
            summary=(
                f"{user.full_name} recorded task [{task.priority}/{task.category}]: "
                f"{task.description[:80]}"
            ),
            metadata={
                "model_suggested_category": task.model_suggested_category,
                "confirmed_category": task.confirmed_category,
                "model_suggested_priority": task.model_suggested_priority,
                "confirmed_priority": task.confirmed_priority,
                "was_overridden": task.was_overridden,
            },
            request=self.request,
        )

    def perform_update(self, serializer):
        task = self.get_object()
        user = self.request.user
        prev_status = task.status
        prev_prio = task.priority

        updated = serializer.save()
        if prev_status != updated.status or prev_prio != updated.priority:
            TaskStatusHistory.objects.create(
                task=updated,
                changed_by=user,
                previous_status=prev_status,
                new_status=updated.status,
                previous_priority=prev_prio,
                new_priority=updated.priority,
                comment=self.request.data.get("status_comment", "Task updated."),
            )
            log_audit_event(
                organisation=user.organisation,
                actor=user,
                action="TASK_UPDATED",
                target_type="Task",
                target_id=updated.id,
                summary=(
                    f"{user.full_name} updated task '{updated.description[:60]}' "
                    f"({prev_status} -> {updated.status}, {prev_prio} -> {updated.priority})."
                ),
                request=self.request,
            )

    @action(detail=True, methods=["post"], url_path="update-status")
    def update_status(self, request, pk=None):
        """Updates a task's operational status (e.g., carried-forward task progressed to In Progress or Completed)."""
        task = self.get_object()
        user = request.user
        new_status = request.data.get("status")
        new_priority = request.data.get("priority", task.priority)
        comment = (request.data.get("comment") or "").strip()

        if new_status not in dict(TaskStatus.choices):
            return Response(
                {"status": [f"Invalid status '{new_status}'. Choose from Pending, In Progress, Completed."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prev_status = task.status
        prev_priority = task.priority
        task.status = new_status
        task.priority = new_priority
        task.confirmed_priority = new_priority
        if comment:
            stamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            note_line = f"[{stamp} - {user.full_name}]: {comment}"
            task.contextual_notes = (
                f"{task.contextual_notes}\n{note_line}".strip()
                if task.contextual_notes
                else note_line
            )
        task.save()

        TaskStatusHistory.objects.create(
            task=task,
            changed_by=user,
            previous_status=prev_status,
            new_status=new_status,
            previous_priority=prev_priority,
            new_priority=new_priority,
            comment=comment or f"Status changed from {prev_status} to {new_status}.",
        )

        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="TASK_STATUS_CHANGED",
            target_type="Task",
            target_id=task.id,
            summary=f"{user.full_name} marked task '{task.description[:60]}' as {new_status}.",
            request=request,
        )

        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)


class AcknowledgmentEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides acknowledgment history for Incoming Workers, Outgoing Workers, Supervisors, and Admins."""

    serializer_class = AcknowledgmentEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["acknowledged_by", "handover_report"]

    def get_queryset(self):
        user = self.request.user
        qs = AcknowledgmentEvent.objects.select_related(
            "handover_report",
            "handover_report__shift",
            "acknowledged_by",
            "organisation",
        ).filter(organisation=user.organisation)

        mine_only = self.request.query_params.get("mine_only")
        if mine_only and mine_only.lower() in ("true", "1"):
            qs = qs.filter(acknowledged_by=user)

        return qs
