import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class ShiftStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class Shift(models.Model):
    """Represents a scheduled or active operational shift with outgoing and incoming worker assignments."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "accounts.Organisation",
        on_delete=models.PROTECT,
        related_name="shifts",
    )
    name = models.CharField(
        max_length=150,
        help_text="Descriptive shift title, e.g., Morning Line Maintenance Shift A",
    )
    department = models.CharField(max_length=120, default="General Operations")
    shift_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    outgoing_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="outgoing_shifts",
    )
    incoming_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="incoming_shifts",
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="supervised_shifts",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=ShiftStatus.choices,
        default=ShiftStatus.ACTIVE,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-shift_date", "-start_time"]
        indexes = [
            models.Index(fields=["organisation", "shift_date", "status"]),
            models.Index(fields=["outgoing_worker", "shift_date"]),
            models.Index(fields=["incoming_worker", "shift_date"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.shift_date} {self.start_time}-{self.end_time})"


class HandoverStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"


class EquipmentStatusChoice(models.TextChoices):
    OPERATIONAL = "OPERATIONAL", "All Systems Operational"
    MINOR_ISSUE = "MINOR_ISSUE", "Minor Issue / Degraded Performance"
    MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED", "Maintenance Required"
    CRITICAL_FAULT = "CRITICAL_FAULT", "Critical Fault / Equipment Grounded"


class HandoverReport(models.Model):
    """Formal shift handover report transferring responsibility from outgoing to incoming worker."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_code = models.CharField(max_length=40, unique=True, db_index=True)
    organisation = models.ForeignKey(
        "accounts.Organisation",
        on_delete=models.PROTECT,
        related_name="handover_reports",
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name="handover_reports",
    )
    submitting_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_handovers",
    )
    designated_incoming_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_handovers",
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="acknowledged_handovers",
        null=True,
        blank=True,
    )
    equipment_status = models.CharField(
        max_length=40,
        choices=EquipmentStatusChoice.choices,
        default=EquipmentStatusChoice.OPERATIONAL,
    )
    equipment_details = models.TextField(blank=True, default="")
    safety_issues = models.TextField(
        blank=True,
        default="",
        help_text="Safety observations, hazards, or near misses recorded during the shift.",
    )
    has_safety_incident = models.BooleanField(default=False)
    additional_notes = models.TextField(blank=True, default="")
    acknowledgment_notes = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=HandoverStatus.choices,
        default=HandoverStatus.DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organisation", "status", "-created_at"]),
            models.Index(fields=["submitting_worker", "status"]),
            models.Index(fields=["designated_incoming_worker", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.report_code:
            date_part = timezone.now().strftime("%Y%m%d")
            short_uid = str(self.id or uuid.uuid4())[:6].upper()
            self.report_code = f"HND-{date_part}-{short_uid}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.report_code} ({self.status})"


class TaskStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    IN_PROGRESS = "In Progress", "In Progress"
    COMPLETED = "Completed", "Completed"


class TaskPriority(models.TextChoices):
    LOW = "Low", "Low"
    MEDIUM = "Medium", "Medium"
    HIGH = "High", "High"
    CRITICAL = "Critical", "Critical"


class Task(models.Model):
    """Structured task record with both NLP-suggested and worker-confirmed classification and priority."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "accounts.Organisation",
        on_delete=models.PROTECT,
        related_name="tasks",
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name="tasks",
    )
    handover_report = models.ForeignKey(
        HandoverReport,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    description = models.TextField()
    category = models.CharField(max_length=80, default="Operations", db_index=True)
    status = models.CharField(
        max_length=25,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
        db_index=True,
    )
    # NLP Provenance & Override Tracking
    model_suggested_category = models.CharField(max_length=80, blank=True, default="")
    model_suggested_priority = models.CharField(max_length=20, blank=True, default="")
    category_confidence = models.FloatField(null=True, blank=True)
    priority_confidence = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Combined or primary model confidence percentage (0-100).",
    )
    nlp_provider_used = models.CharField(max_length=80, blank=True, default="")
    confirmed_category = models.CharField(max_length=80, blank=True, default="")
    confirmed_priority = models.CharField(max_length=20, blank=True, default="")
    was_overridden = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    due_date = models.DateTimeField(null=True, blank=True)
    contextual_notes = models.TextField(blank=True, default="")
    carried_forward_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carried_forward_instances",
    )
    is_carried_forward = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organisation", "status", "priority"]),
            models.Index(fields=["shift", "status"]),
            models.Index(fields=["assignee", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.confirmed_category:
            self.confirmed_category = self.category
        else:
            self.category = self.confirmed_category

        if not self.confirmed_priority:
            self.confirmed_priority = self.priority
        else:
            self.priority = self.confirmed_priority

        if self.model_suggested_category or self.model_suggested_priority:
            cat_diff = (
                bool(self.model_suggested_category)
                and self.model_suggested_category.lower() != self.confirmed_category.lower()
            )
            prio_diff = (
                bool(self.model_suggested_priority)
                and self.model_suggested_priority.lower() != self.confirmed_priority.lower()
            )
            self.was_overridden = cat_diff or prio_diff

        if self.status == TaskStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != TaskStatus.COMPLETED:
            self.completed_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.priority}] {self.description[:50]} ({self.status})"


class AcknowledgmentEvent(models.Model):
    """Immutable audit record created when an incoming worker formally acknowledges a handover."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "accounts.Organisation",
        on_delete=models.PROTECT,
        related_name="acknowledgment_events",
    )
    handover_report = models.ForeignKey(
        HandoverReport,
        on_delete=models.PROTECT,
        related_name="acknowledgment_events",
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="acknowledgment_records",
    )
    acknowledgment_notes = models.TextField(blank=True, default="")
    unresolved_tasks_count = models.PositiveIntegerField(default=0)
    critical_tasks_count = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-acknowledged_at"]

    def __str__(self):
        return f"Ack {self.handover_report.report_code} by {self.acknowledged_by_id} at {self.acknowledged_at}"


class TaskStatusHistory(models.Model):
    """Immutable audit trail tracking status and priority transitions of individual tasks across shifts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT,
        related_name="history",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="task_changes",
    )
    previous_status = models.CharField(max_length=25, blank=True, default="")
    new_status = models.CharField(max_length=25)
    previous_priority = models.CharField(max_length=20, blank=True, default="")
    new_priority = models.CharField(max_length=20, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class HandoverAmendment(models.Model):
    """Auditable amendment record for authorised post-submission corrections without rewriting history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    handover_report = models.ForeignKey(
        HandoverReport,
        on_delete=models.PROTECT,
        related_name="amendments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="handover_amendments",
    )
    amendment_reason = models.CharField(max_length=255)
    amendment_details = models.TextField()
    updated_equipment_status = models.CharField(max_length=40, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
