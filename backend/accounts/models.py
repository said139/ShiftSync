import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


def default_task_categories():
    return [
        "Flight Operations",
        "Aircraft Maintenance",
        "Cabin Operations",
        "Safety Follow-up",
        "Equipment",
        "Documentation",
        "General Operations",
        "Maintenance",
        "Safety & Compliance",
        "Equipment Check",
        "Operations",
        "Inventory",
        "Customer Service",
        "Administration",
        "Other",
    ]


def default_priority_levels():
    return ["Low", "Medium", "High", "Critical"]


class Organisation(models.Model):
    """Represents a shift-based aviation organisation or enterprise unit with isolated operational data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180, unique=True)
    code = models.CharField(max_length=40, unique=True, db_index=True)
    industry = models.CharField(
        max_length=120, default="Commercial Aviation & Aircraft Maintenance Operations"
    )
    departments = models.JSONField(
        default=list,
        blank=True,
        help_text="List of configured aviation departments/operational units within the organisation.",
    )
    task_categories = models.JSONField(
        default=default_task_categories,
        help_text="Configurable task categories for manual selection and NLP mapping.",
    )
    priority_levels = models.JSONField(
        default=default_priority_levels,
        help_text="Configured priority levels.",
    )
    require_acknowledgment_notes = models.BooleanField(default=False)
    require_account_approval = models.BooleanField(
        default=False,
        help_text="When enabled, public sign-up accounts start in PENDING status until approved by a Supervisor or Admin.",
    )
    low_confidence_threshold = models.FloatField(default=60.0)
    nlp_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class UserRole(models.TextChoices):
    OUTGOING_WORKER = "OUTGOING_WORKER", "Outgoing Worker"
    INCOMING_WORKER = "INCOMING_WORKER", "Incoming Worker"
    SUPERVISOR = "SUPERVISOR", "Supervisor"
    ADMIN = "ADMIN", "System Administrator"


class PersonnelCategory(models.TextChoices):
    PILOT = "PILOT", "Pilot / Flight Crew"
    ENGINEER = "ENGINEER", "Aeronautical Engineer / Aircraft Maintenance"
    CABIN_CREW = "CABIN_CREW", "Cabin Crew / Flight Attendant"
    OPS_SUPERVISOR = "OPS_SUPERVISOR", "Operations Supervisor"
    SYSTEM_ADMIN = "SYSTEM_ADMIN", "System Administrator"


class AccountApprovalStatus(models.TextChoices):
    APPROVED = "APPROVED", "Approved"
    PENDING = "PENDING", "Pending Approval"
    REJECTED = "REJECTED", "Rejected"


class UserManager(BaseUserManager):
    """Custom manager for email-based authentication."""

    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have a valid email address.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, full_name=full_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name="System Administrator", password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("personnel_category", PersonnelCategory.SYSTEM_ADMIN)
        extra_fields.setdefault("approval_status", AccountApprovalStatus.APPROVED)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if "organisation" not in extra_fields or extra_fields["organisation"] is None:
            org, _ = Organisation.objects.get_or_create(
                code="KQ-MRO",
                defaults={
                    "name": "ShiftSync Aviation Operations (JKIA Hub)",
                    "departments": [
                        "Flight Operations (B787 / B737 Fleet)",
                        "Line Maintenance & Hangar Engineering",
                        "Avionics & Flight Control Systems",
                        "Cabin Services & In-Flight Operations",
                        "Safety & Quality Assurance",
                        "IT & Systems Governance",
                    ],
                },
            )
            extra_fields["organisation"] = org

        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with aviation personnel categories, role-based permissions, and organisation scoping."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    employee_id = models.CharField(max_length=50, blank=True, default="", db_index=True)
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.OUTGOING_WORKER,
        db_index=True,
    )
    personnel_category = models.CharField(
        max_length=30,
        choices=PersonnelCategory.choices,
        default=PersonnelCategory.ENGINEER,
        db_index=True,
    )
    approval_status = models.CharField(
        max_length=20,
        choices=AccountApprovalStatus.choices,
        default=AccountApprovalStatus.APPROVED,
        db_index=True,
    )
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name="users",
    )
    department = models.CharField(max_length=120, default="Line Maintenance & Hangar Engineering")
    phone_number = models.CharField(max_length=40, blank=True, default="")
    privacy_terms_accepted = models.BooleanField(default=True)
    privacy_terms_accepted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["organisation", "role"]),
            models.Index(fields=["organisation", "personnel_category"]),
            models.Index(fields=["organisation", "is_active", "approval_status"]),
        ]

    def save(self, *args, **kwargs):
        if self.role == UserRole.ADMIN and self.personnel_category not in (
            PersonnelCategory.SYSTEM_ADMIN,
            PersonnelCategory.PILOT,
            PersonnelCategory.ENGINEER,
            PersonnelCategory.CABIN_CREW,
        ):
            self.personnel_category = PersonnelCategory.SYSTEM_ADMIN
        elif self.role == UserRole.SUPERVISOR and not self.personnel_category:
            self.personnel_category = PersonnelCategory.OPS_SUPERVISOR
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} <{self.email}> ({self.personnel_category} / {self.role})"


class PasswordResetToken(models.Model):
    """Stores time-limited password recovery tokens for auditable password reset workflows."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def is_valid(self):
        return (not self.used) and (timezone.now() <= self.expires_at)


class AuditEvent(models.Model):
    """Immutable audit log preserving accountability across critical handover and system events."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=80, db_index=True)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=100, db_index=True)
    summary = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organisation", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"[{self.created_at.isoformat()}] {self.action} ({self.target_type}:{self.target_id})"
