from django.db import transaction
from rest_framework import serializers

from accounts.models import User
from .models import (
    AcknowledgmentEvent,
    HandoverAmendment,
    HandoverReport,
    HandoverStatus,
    Shift,
    Task,
    TaskStatus,
    TaskStatusHistory,
)


class ShiftSerializer(serializers.ModelSerializer):
    outgoing_worker_name = serializers.CharField(
        source="outgoing_worker.full_name", read_only=True
    )
    outgoing_worker_email = serializers.CharField(
        source="outgoing_worker.email", read_only=True
    )
    incoming_worker_name = serializers.CharField(
        source="incoming_worker.full_name", read_only=True
    )
    incoming_worker_email = serializers.CharField(
        source="incoming_worker.email", read_only=True
    )
    supervisor_name = serializers.CharField(
        source="supervisor.full_name", read_only=True, default=""
    )
    organisation_name = serializers.CharField(
        source="organisation.name", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    handover_count = serializers.IntegerField(
        source="handover_reports.count", read_only=True
    )

    class Meta:
        model = Shift
        fields = [
            "id",
            "organisation",
            "organisation_name",
            "name",
            "department",
            "shift_date",
            "start_time",
            "end_time",
            "outgoing_worker",
            "outgoing_worker_name",
            "outgoing_worker_email",
            "incoming_worker",
            "incoming_worker_name",
            "incoming_worker_email",
            "supervisor",
            "supervisor_name",
            "status",
            "status_display",
            "notes",
            "handover_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organisation", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        org = request.user.organisation if request and request.user else None

        outgoing = attrs.get(
            "outgoing_worker",
            getattr(self.instance, "outgoing_worker", None),
        )
        incoming = attrs.get(
            "incoming_worker",
            getattr(self.instance, "incoming_worker", None),
        )
        supervisor = attrs.get(
            "supervisor",
            getattr(self.instance, "supervisor", None),
        )

        if outgoing and incoming and outgoing.id == incoming.id:
            raise serializers.ValidationError(
                {
                    "incoming_worker": (
                        "The designated incoming worker must be different from the outgoing worker."
                    )
                }
            )

        if org:
            for field_name, worker in [
                ("outgoing_worker", outgoing),
                ("incoming_worker", incoming),
                ("supervisor", supervisor),
            ]:
                if worker and worker.organisation_id != org.id:
                    raise serializers.ValidationError(
                        {
                            field_name: "Selected user does not belong to your organisation."
                        }
                    )
                if worker and not worker.is_active:
                    raise serializers.ValidationError(
                        {field_name: "Selected user account is inactive."}
                    )

        return attrs


class TaskStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(
        source="changed_by.full_name", read_only=True
    )
    changed_by_role = serializers.CharField(source="changed_by.role", read_only=True)

    class Meta:
        model = TaskStatusHistory
        fields = [
            "id",
            "task",
            "changed_by",
            "changed_by_name",
            "changed_by_role",
            "previous_status",
            "new_status",
            "previous_priority",
            "new_priority",
            "comment",
            "created_at",
        ]
        read_only_fields = fields


class TaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    assignee_name = serializers.CharField(
        source="assignee.full_name", read_only=True, default=""
    )
    shift_name = serializers.CharField(source="shift.name", read_only=True)
    shift_date = serializers.DateField(source="shift.shift_date", read_only=True)
    handover_code = serializers.CharField(
        source="handover_report.report_code", read_only=True, default=""
    )
    history = TaskStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "organisation",
            "shift",
            "shift_name",
            "shift_date",
            "handover_report",
            "handover_code",
            "description",
            "category",
            "status",
            "priority",
            "model_suggested_category",
            "model_suggested_priority",
            "category_confidence",
            "priority_confidence",
            "confidence_score",
            "nlp_provider_used",
            "confirmed_category",
            "confirmed_priority",
            "was_overridden",
            "created_by",
            "created_by_name",
            "assignee",
            "assignee_name",
            "due_date",
            "contextual_notes",
            "carried_forward_from",
            "is_carried_forward",
            "completed_at",
            "created_at",
            "updated_at",
            "history",
        ]
        read_only_fields = [
            "id",
            "organisation",
            "created_by",
            "was_overridden",
            "completed_at",
            "created_at",
            "updated_at",
            "history",
        ]

    def validate_description(self, value):
        cleaned = (value or "").strip()
        if len(cleaned) < 5:
            raise serializers.ValidationError(
                "Task description must be at least 5 characters long."
            )
        return cleaned


class NestedTaskInputSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False, allow_null=True)
    description = serializers.CharField(min_length=5)
    category = serializers.CharField(required=False, default="Operations")
    status = serializers.ChoiceField(
        choices=TaskStatus.choices, default=TaskStatus.PENDING
    )
    priority = serializers.CharField(required=False, default="Medium")
    model_suggested_category = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    model_suggested_priority = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    category_confidence = serializers.FloatField(required=False, allow_null=True)
    priority_confidence = serializers.FloatField(required=False, allow_null=True)
    confidence_score = serializers.FloatField(required=False, allow_null=True)
    nlp_provider_used = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    confirmed_category = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    confirmed_priority = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    contextual_notes = serializers.CharField(
        required=False, allow_blank=True, default=""
    )


class AcknowledgmentEventSerializer(serializers.ModelSerializer):
    acknowledged_by_name = serializers.CharField(
        source="acknowledged_by.full_name", read_only=True
    )
    acknowledged_by_email = serializers.CharField(
        source="acknowledged_by.email", read_only=True
    )
    handover_code = serializers.CharField(
        source="handover_report.report_code", read_only=True
    )
    shift_name = serializers.CharField(
        source="handover_report.shift.name", read_only=True
    )

    class Meta:
        model = AcknowledgmentEvent
        fields = [
            "id",
            "organisation",
            "handover_report",
            "handover_code",
            "shift_name",
            "acknowledged_by",
            "acknowledged_by_name",
            "acknowledged_by_email",
            "acknowledgment_notes",
            "unresolved_tasks_count",
            "critical_tasks_count",
            "ip_address",
            "acknowledged_at",
        ]
        read_only_fields = fields


class HandoverAmendmentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_role = serializers.CharField(source="author.role", read_only=True)

    class Meta:
        model = HandoverAmendment
        fields = [
            "id",
            "handover_report",
            "author",
            "author_name",
            "author_role",
            "amendment_reason",
            "amendment_details",
            "updated_equipment_status",
            "created_at",
        ]
        read_only_fields = ["id", "handover_report", "author", "created_at"]


class HandoverReportSerializer(serializers.ModelSerializer):
    shift_details = ShiftSerializer(source="shift", read_only=True)
    submitting_worker_name = serializers.CharField(
        source="submitting_worker.full_name", read_only=True
    )
    submitting_worker_email = serializers.CharField(
        source="submitting_worker.email", read_only=True
    )
    designated_incoming_worker_name = serializers.CharField(
        source="designated_incoming_worker.full_name", read_only=True
    )
    designated_incoming_worker_email = serializers.CharField(
        source="designated_incoming_worker.email", read_only=True
    )
    acknowledged_by_name = serializers.CharField(
        source="acknowledged_by.full_name", read_only=True, default=""
    )
    equipment_status_display = serializers.CharField(
        source="get_equipment_status_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    tasks_input = NestedTaskInputSerializer(many=True, write_only=True, required=False)
    acknowledgment_events = AcknowledgmentEventSerializer(many=True, read_only=True)
    amendments = HandoverAmendmentSerializer(many=True, read_only=True)

    total_tasks = serializers.SerializerMethodField()
    unresolved_tasks = serializers.SerializerMethodField()
    critical_tasks = serializers.SerializerMethodField()

    class Meta:
        model = HandoverReport
        fields = [
            "id",
            "report_code",
            "organisation",
            "shift",
            "shift_details",
            "submitting_worker",
            "submitting_worker_name",
            "submitting_worker_email",
            "designated_incoming_worker",
            "designated_incoming_worker_name",
            "designated_incoming_worker_email",
            "acknowledged_by",
            "acknowledged_by_name",
            "equipment_status",
            "equipment_status_display",
            "equipment_details",
            "safety_issues",
            "has_safety_incident",
            "additional_notes",
            "acknowledgment_notes",
            "status",
            "status_display",
            "created_at",
            "updated_at",
            "submitted_at",
            "acknowledged_at",
            "tasks",
            "tasks_input",
            "acknowledgment_events",
            "amendments",
            "total_tasks",
            "unresolved_tasks",
            "critical_tasks",
        ]
        read_only_fields = [
            "id",
            "report_code",
            "organisation",
            "submitting_worker",
            "acknowledged_by",
            "status",
            "created_at",
            "updated_at",
            "submitted_at",
            "acknowledged_at",
        ]

    def get_total_tasks(self, obj):
        return obj.tasks.count()

    def get_unresolved_tasks(self, obj):
        return obj.tasks.exclude(status=TaskStatus.COMPLETED).count()

    def get_critical_tasks(self, obj):
        return obj.tasks.filter(priority="Critical").count()

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        if self.instance and self.instance.status != HandoverStatus.DRAFT:
            raise serializers.ValidationError(
                "Submitted or Acknowledged handover reports cannot be edited directly. Use the authorised amendment workflow."
            )

        shift = attrs.get("shift", getattr(self.instance, "shift", None))
        incoming = attrs.get(
            "designated_incoming_worker",
            getattr(self.instance, "designated_incoming_worker", None),
        )

        if user and shift and shift.organisation_id != user.organisation_id:
            raise serializers.ValidationError(
                {"shift": "Selected shift belongs to another organisation."}
            )

        if user and incoming:
            if incoming.organisation_id != user.organisation_id:
                raise serializers.ValidationError(
                    {
                        "designated_incoming_worker": "Designated incoming worker must belong to your organisation."
                    }
                )
            submitting = (
                self.instance.submitting_worker if self.instance else user
            )
            if incoming.id == submitting.id:
                raise serializers.ValidationError(
                    {
                        "designated_incoming_worker": "Outgoing and designated incoming worker cannot be the same person."
                    }
                )

        return attrs

    def _sync_tasks(self, report, tasks_data, user):
        existing_tasks = {str(t.id): t for t in report.tasks.all()}
        kept_ids = set()

        for item in tasks_data:
            task_id = str(item.get("id")) if item.get("id") else None
            confirmed_cat = item.get("confirmed_category") or item.get("category") or "Operations"
            confirmed_prio = item.get("confirmed_priority") or item.get("priority") or "Medium"

            if task_id and task_id in existing_tasks:
                t_obj = existing_tasks[task_id]
                prev_status = t_obj.status
                prev_prio = t_obj.priority

                t_obj.description = item["description"].strip()
                t_obj.category = confirmed_cat
                t_obj.confirmed_category = confirmed_cat
                t_obj.priority = confirmed_prio
                t_obj.confirmed_priority = confirmed_prio
                t_obj.status = item.get("status", t_obj.status)
                t_obj.model_suggested_category = item.get(
                    "model_suggested_category", t_obj.model_suggested_category
                )
                t_obj.model_suggested_priority = item.get(
                    "model_suggested_priority", t_obj.model_suggested_priority
                )
                t_obj.category_confidence = item.get(
                    "category_confidence", t_obj.category_confidence
                )
                t_obj.priority_confidence = item.get(
                    "priority_confidence", t_obj.priority_confidence
                )
                t_obj.confidence_score = item.get(
                    "confidence_score", t_obj.confidence_score
                )
                t_obj.nlp_provider_used = item.get(
                    "nlp_provider_used", t_obj.nlp_provider_used
                )
                t_obj.assignee = item.get(
                    "assignee", report.designated_incoming_worker
                )
                t_obj.due_date = item.get("due_date", t_obj.due_date)
                t_obj.contextual_notes = item.get(
                    "contextual_notes", t_obj.contextual_notes
                )
                t_obj.save()
                kept_ids.add(task_id)

                if prev_status != t_obj.status or prev_prio != t_obj.priority:
                    TaskStatusHistory.objects.create(
                        task=t_obj,
                        changed_by=user,
                        previous_status=prev_status,
                        new_status=t_obj.status,
                        previous_priority=prev_prio,
                        new_priority=t_obj.priority,
                        comment="Updated in handover draft.",
                    )
            else:
                new_task = Task.objects.create(
                    organisation=report.organisation,
                    shift=report.shift,
                    handover_report=report,
                    description=item["description"].strip(),
                    category=confirmed_cat,
                    confirmed_category=confirmed_cat,
                    status=item.get("status", TaskStatus.PENDING),
                    priority=confirmed_prio,
                    confirmed_priority=confirmed_prio,
                    model_suggested_category=item.get("model_suggested_category", ""),
                    model_suggested_priority=item.get("model_suggested_priority", ""),
                    category_confidence=item.get("category_confidence"),
                    priority_confidence=item.get("priority_confidence"),
                    confidence_score=item.get("confidence_score"),
                    nlp_provider_used=item.get("nlp_provider_used", ""),
                    created_by=user,
                    assignee=item.get("assignee") or report.designated_incoming_worker,
                    due_date=item.get("due_date"),
                    contextual_notes=item.get("contextual_notes", ""),
                )
                kept_ids.add(str(new_task.id))
                TaskStatusHistory.objects.create(
                    task=new_task,
                    changed_by=user,
                    previous_status="",
                    new_status=new_task.status,
                    previous_priority="",
                    new_priority=new_task.priority,
                    comment="Recorded during handover preparation.",
                )

        # Remove draft tasks that the user explicitly deleted from the draft form
        for old_id, old_task in existing_tasks.items():
            if old_id not in kept_ids:
                old_task.history.all().delete()
                old_task.delete()

    @transaction.atomic
    def create(self, validated_data):
        tasks_data = validated_data.pop("tasks_input", None)
        request = self.context.get("request")
        user = request.user
        report = HandoverReport.objects.create(
            organisation=user.organisation,
            submitting_worker=user,
            status=HandoverStatus.DRAFT,
            **validated_data,
        )
        if tasks_data is not None:
            self._sync_tasks(report, tasks_data, user)
        return report

    @transaction.atomic
    def update(self, instance, validated_data):
        tasks_data = validated_data.pop("tasks_input", None)
        request = self.context.get("request")
        user = request.user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tasks_data is not None:
            self._sync_tasks(instance, tasks_data, user)
        return instance
