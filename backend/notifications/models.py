import uuid
from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    HANDOVER_SUBMITTED = "HANDOVER_SUBMITTED", "Handover Submitted / Requires Acknowledgement"
    HANDOVER_ACKNOWLEDGED = "HANDOVER_ACKNOWLEDGED", "Handover Acknowledged"
    HANDOVER_AMENDED = "HANDOVER_AMENDED", "Handover Amended"
    TASK_ASSIGNED = "TASK_ASSIGNED", "Task Assigned"
    TASK_OVERDUE = "TASK_OVERDUE", "Task Overdue"
    TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED", "Task Status Changed"
    ACCOUNT_APPROVAL_REQUIRED = "ACCOUNT_APPROVAL_REQUIRED", "Account Approval Required"
    CRITICAL_TASK = "CRITICAL_TASK", "Critical Priority Task"
    SHIFT_ASSIGNED = "SHIFT_ASSIGNED", "Shift / Duty Assignment"
    SYSTEM = "SYSTEM", "System Notification"


class Notification(models.Model):
    """Persistent in-app notification for aviation handover and operational events."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "accounts.Organisation",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        db_index=True,
    )
    related_handover = models.ForeignKey(
        "operations.HandoverReport",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    related_task = models.ForeignKey(
        "operations.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["organisation", "-created_at"]),
        ]

    def __str__(self):
        return f"[{self.notification_type}] To {self.recipient_id}: {self.title}"
