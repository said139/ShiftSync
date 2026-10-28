from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from .models import (
    AccountApprovalStatus,
    AuditEvent,
    Organisation,
    PersonnelCategory,
    User,
    UserRole,
)


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = [
            "id",
            "name",
            "code",
            "industry",
            "departments",
            "task_categories",
            "priority_levels",
            "require_acknowledgment_notes",
            "require_account_approval",
            "low_confidence_threshold",
            "nlp_enabled",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(
        source="organisation.name", read_only=True
    )
    organisation_code = serializers.CharField(
        source="organisation.code", read_only=True
    )
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    personnel_category_display = serializers.CharField(
        source="get_personnel_category_display", read_only=True
    )
    approval_status_display = serializers.CharField(
        source="get_approval_status_display", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "employee_id",
            "role",
            "role_display",
            "personnel_category",
            "personnel_category_display",
            "approval_status",
            "approval_status_display",
            "organisation",
            "organisation_name",
            "organisation_code",
            "department",
            "phone_number",
            "privacy_terms_accepted",
            "is_active",
            "last_login",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_login", "created_at", "updated_at"]


ALLOWED_PUBLIC_CATEGORIES = {
    PersonnelCategory.PILOT,
    PersonnelCategory.ENGINEER,
    PersonnelCategory.CABIN_CREW,
}

DEFAULT_DEPARTMENT_BY_CATEGORY = {
    PersonnelCategory.PILOT: "Flight Operations (B787 / B737 Fleet)",
    PersonnelCategory.ENGINEER: "Line Maintenance & Hangar Engineering",
    PersonnelCategory.CABIN_CREW: "Cabin Services & In-Flight Operations",
}


class PublicRegistrationSerializer(serializers.Serializer):
    """
    Validates self-registration for ShiftSync Aviation crew members.
    Strictly prevents privilege escalation to Supervisor or Administrator roles.
    """

    full_name = serializers.CharField(max_length=150, min_length=2)
    email = serializers.EmailField()
    employee_id = serializers.CharField(max_length=50, min_length=3)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    personnel_category = serializers.CharField(max_length=30)
    department = serializers.CharField(
        max_length=120, required=False, allow_blank=True, default=""
    )
    phone_number = serializers.CharField(
        max_length=40, required=False, allow_blank=True, default=""
    )
    privacy_terms_accepted = serializers.BooleanField()
    role = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_email(self, value):
        email = (value or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "An account with this work email address already exists."
            )
        return email

    def validate_employee_id(self, value):
        emp_id = (value or "").strip().upper()
        if len(emp_id) < 3:
            raise serializers.ValidationError(
                "Employee / Staff ID must be at least 3 characters."
            )
        if User.objects.filter(employee_id__iexact=emp_id).exists():
            raise serializers.ValidationError(
                "An account with this Employee / Staff ID already exists."
            )
        return emp_id

    def validate_personnel_category(self, value):
        cat = (value or "").strip().upper()
        if cat not in ALLOWED_PUBLIC_CATEGORIES:
            raise serializers.ValidationError(
                "Public registration is restricted to operational aviation personnel: "
                "Pilot / Flight Crew (PILOT), Aeronautical Engineer / Aircraft Maintenance (ENGINEER), "
                "or Cabin Crew / Flight Attendant (CABIN_CREW). Privileged roles cannot be self-selected."
            )
        return cat

    def validate_privacy_terms_accepted(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "You must accept the ShiftSync Aviation privacy policy and operational terms."
            )
        return value

    def validate(self, attrs):
        requested_role = (attrs.get("role") or "").strip().upper()
        if requested_role in (UserRole.SUPERVISOR, UserRole.ADMIN, "OPS_SUPERVISOR", "SYSTEM_ADMIN"):
            raise serializers.ValidationError(
                {
                    "role": "Unauthorised role selection. Public registration cannot grant Supervisor or Administrator privileges."
                }
            )

        pw = attrs.get("password") or ""
        confirm_pw = attrs.get("confirm_password") or ""
        if pw != confirm_pw:
            raise serializers.ValidationError(
                {"confirm_password": "Password confirmation does not match."}
            )
        validate_password(pw)
        return attrs

    def create(self, validated_data):
        org = Organisation.objects.first()
        if not org:
            org = Organisation.objects.create(
                code="KQ-MRO",
                name="ShiftSync Aviation Operations (JKIA Hub)",
                departments=[
                    "Flight Operations (B787 / B737 Fleet)",
                    "Line Maintenance & Hangar Engineering",
                    "Avionics & Flight Control Systems",
                    "Cabin Services & In-Flight Operations",
                    "Safety & Quality Assurance",
                    "IT & Systems Governance",
                ],
            )

        cat = validated_data["personnel_category"]
        dept = (validated_data.get("department") or "").strip()
        if not dept:
            dept = DEFAULT_DEPARTMENT_BY_CATEGORY.get(cat, "General Operations")

        approval_status = (
            AccountApprovalStatus.PENDING
            if org.require_account_approval
            else AccountApprovalStatus.APPROVED
        )

        user = User(
            email=validated_data["email"],
            full_name=validated_data["full_name"].strip(),
            employee_id=validated_data["employee_id"],
            role=UserRole.OUTGOING_WORKER,
            personnel_category=cat,
            approval_status=approval_status,
            organisation=org,
            department=dept,
            phone_number=(validated_data.get("phone_number") or "").strip(),
            privacy_terms_accepted=True,
            privacy_terms_accepted_at=timezone.now(),
            is_active=True,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=False, min_length=8
    )
    organisation = serializers.PrimaryKeyRelatedField(
        queryset=Organisation.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "employee_id",
            "role",
            "personnel_category",
            "approval_status",
            "organisation",
            "department",
            "phone_number",
            "is_active",
            "password",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        email = value.strip().lower()
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_employee_id(self, value):
        emp_id = (value or "").strip().upper()
        if emp_id:
            qs = User.objects.filter(employee_id__iexact=emp_id)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "A user with this Employee / Staff ID already exists."
                )
        return emp_id

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        request = self.context.get("request")
        if "organisation" not in validated_data or validated_data["organisation"] is None:
            if request and request.user and request.user.is_authenticated:
                validated_data["organisation"] = request.user.organisation
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_password("ShiftSync@2026!")
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "full_name",
            "phone_number",
            "department",
            "employee_id",
            "personnel_category",
        ]

    def validate_personnel_category(self, value):
        request = self.context.get("request")
        user = request.user if request else None
        if user and user.role not in (UserRole.ADMIN, UserRole.SUPERVISOR):
            if value not in ALLOWED_PUBLIC_CATEGORIES:
                raise serializers.ValidationError(
                    "Operational personnel may only select Pilot, Engineer, or Cabin Crew categories."
                )
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordRecoveryRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True, default="System")
    actor_email = serializers.CharField(source="actor.email", read_only=True, default="")
    actor_role = serializers.CharField(source="actor.role", read_only=True, default="")
    organisation_name = serializers.CharField(
        source="organisation.name", read_only=True, default=""
    )

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "organisation",
            "organisation_name",
            "actor",
            "actor_name",
            "actor_email",
            "actor_role",
            "action",
            "target_type",
            "target_id",
            "summary",
            "metadata",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
