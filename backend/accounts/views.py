import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from notifications.models import Notification, NotificationType
from common.ws_broadcast import push_ws_event_to_org, push_ws_event_to_user
from .email_service import send_password_reset_email, send_smtp_diagnostic_test
from .models import (
    AccountApprovalStatus,
    AuditEvent,
    Organisation,
    PasswordResetToken,
    User,
    UserRole,
)
from .permissions import IsSupervisorOrAdmin, IsSystemAdmin
from .serializers import (
    AuditEventSerializer,
    ChangePasswordSerializer,
    OrganisationSerializer,
    PasswordRecoveryRequestSerializer,
    PasswordResetConfirmSerializer,
    ProfileUpdateSerializer,
    PublicRegistrationSerializer,
    UserCreateUpdateSerializer,
    UserSerializer,
)

REFRESH_COOKIE_NAME = "shiftsync_refresh_token"


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_audit_event(
    *,
    organisation=None,
    actor=None,
    action="",
    target_type="",
    target_id="",
    summary="",
    metadata=None,
    request=None,
):
    ip_addr = get_client_ip(request) if request else None
    if organisation is None and actor is not None:
        organisation = getattr(actor, "organisation", None)
    return AuditEvent.objects.create(
        organisation=organisation,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        summary=summary,
        metadata=metadata or {},
        ip_address=ip_addr,
    )


def set_refresh_cookie(response, refresh_token_str, remember_me=True):
    max_age = (7 * 24 * 3600) if remember_me else None
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token_str,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=max_age,
        path="/",
    )


class RegisterAPIView(APIView):
    """
    POST /api/auth/register/
    Public registration endpoint for ShiftSync Aviation personnel (Pilots, Aeronautical Engineers, Cabin Crew).
    Prevents self-assignment of Supervisor or Administrator privileges.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PublicRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="USER_REGISTERED",
            target_type="User",
            target_id=user.id,
            summary=(
                f"New aviation crew account registered: {user.full_name} "
                f"({user.email}, Staff ID: {user.employee_id}, Category: {user.personnel_category}, "
                f"Status: {user.approval_status})."
            ),
            metadata={
                "employee_id": user.employee_id,
                "personnel_category": user.personnel_category,
                "department": user.department,
                "approval_status": user.approval_status,
            },
            request=request,
        )

        # Notify Supervisors and Admins of new registration / approval request
        approvers = User.objects.filter(
            organisation=user.organisation,
            role__in=[UserRole.SUPERVISOR, UserRole.ADMIN],
            is_active=True,
        )
        notif_type = (
            NotificationType.ACCOUNT_APPROVAL_REQUIRED
            if user.approval_status == AccountApprovalStatus.PENDING
            else NotificationType.SYSTEM
        )
        notif_title = (
            f"Account Approval Required: {user.full_name} ({user.employee_id})"
            if user.approval_status == AccountApprovalStatus.PENDING
            else f"New Crew Member Registered: {user.full_name} ({user.employee_id})"
        )
        for sup in approvers:
            notif = Notification.objects.create(
                organisation=user.organisation,
                recipient=sup,
                notification_type=notif_type,
                title=notif_title,
                message=(
                    f"{user.full_name} ({user.get_personnel_category_display()}, Staff ID: {user.employee_id}) "
                    f"registered in department '{user.department}'."
                ),
            )
            push_ws_event_to_user(
                sup.id,
                "NEW_NOTIFICATION",
                {
                    "id": str(notif.id),
                    "title": notif.title,
                    "message": notif.message,
                    "type": notif.notification_type,
                    "created_at": notif.created_at.isoformat(),
                },
            )

        if user.approval_status == AccountApprovalStatus.PENDING:
            return Response(
                {
                    "detail": (
                        "Registration submitted. Your account is pending operational verification "
                        "by a Supervisor or System Administrator."
                    ),
                    "requires_approval": True,
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )

        refresh = RefreshToken.for_user(user)
        access_str = str(refresh.access_token)
        refresh_str = str(refresh)

        response = Response(
            {
                "detail": "Account created successfully.",
                "requires_approval": False,
                "access": access_str,
                "refresh": refresh_str,
                "user": UserSerializer(user).data,
                "organisation": OrganisationSerializer(user.organisation).data,
            },
            status=status.HTTP_201_CREATED,
        )
        set_refresh_cookie(response, refresh_str, remember_me=True)
        return response


class LoginAPIView(APIView):
    """
    Authenticates an aviation user by Work Email OR Employee/Staff ID and returns
    a short-lived JWT access token plus an HttpOnly refresh cookie.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        raw_identifier = (
            request.data.get("email")
            or request.data.get("identifier")
            or ""
        ).strip()
        password = request.data.get("password") or ""
        remember_me = request.data.get("remember_me", True)

        if not raw_identifier or not password:
            return Response(
                {"detail": "Both work email (or Employee ID) and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Look up by email or employee_id
        user_obj = (
            User.objects.select_related("organisation")
            .filter(
                Q(email__iexact=raw_identifier)
                | (~Q(employee_id="") & Q(employee_id__iexact=raw_identifier))
            )
            .first()
        )

        if user_obj and user_obj.approval_status == AccountApprovalStatus.PENDING:
            log_audit_event(
                organisation=user_obj.organisation,
                actor=user_obj,
                action="LOGIN_BLOCKED_PENDING_APPROVAL",
                target_type="User",
                target_id=user_obj.id,
                summary=f"Pending-approval account {user_obj.email} attempted to sign in.",
                request=request,
            )
            return Response(
                {
                    "detail": (
                        "Your account is pending approval by an Operations Supervisor or System Administrator."
                    ),
                    "code": "pending_approval",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if user_obj and (
            not user_obj.is_active
            or user_obj.approval_status == AccountApprovalStatus.REJECTED
        ):
            log_audit_event(
                organisation=user_obj.organisation,
                actor=user_obj,
                action="LOGIN_BLOCKED_INACTIVE",
                target_type="User",
                target_id=user_obj.id,
                summary=f"Deactivated/rejected account {user_obj.email} attempted to log in.",
                request=request,
            )
            return Response(
                {
                    "detail": (
                        "This account has been deactivated or suspended. Contact your System Administrator."
                    ),
                    "code": "account_disabled",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        auth_email = user_obj.email if user_obj else raw_identifier.lower()
        user = authenticate(request=request, email=auth_email, password=password)
        if user is None:
            log_audit_event(
                organisation=user_obj.organisation if user_obj else None,
                actor=user_obj,
                action="LOGIN_FAILED",
                target_type="User",
                target_id=raw_identifier,
                summary=f"Failed login attempt for identifier '{raw_identifier}'.",
                request=request,
            )
            return Response(
                {"detail": "Invalid email/Employee ID or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)
        access_str = str(refresh.access_token)
        refresh_str = str(refresh)

        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="USER_LOGIN",
            target_type="User",
            target_id=user.id,
            summary=f"{user.full_name} ({user.personnel_category} / {user.role}) signed in.",
            request=request,
        )

        response = Response(
            {
                "access": access_str,
                "refresh": refresh_str,
                "user": UserSerializer(user).data,
                "organisation": OrganisationSerializer(user.organisation).data,
            },
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, refresh_str, remember_me=bool(remember_me))
        return response


class RefreshTokenAPIView(APIView):
    """Refreshes an access token using either an HttpOnly cookie or explicit refresh token payload."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        raw_refresh = request.data.get("refresh") or request.COOKIES.get(
            REFRESH_COOKIE_NAME
        )
        if not raw_refresh:
            return Response(
                {"detail": "No refresh token provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(raw_refresh)
            user_id = refresh.get("user_id")
            user = (
                User.objects.select_related("organisation")
                .filter(
                    id=user_id,
                    is_active=True,
                    approval_status=AccountApprovalStatus.APPROVED,
                )
                .first()
            )
            if not user:
                return Response(
                    {"detail": "User account is inactive, pending approval, or no longer exists."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            access_str = str(refresh.access_token)
            new_refresh = RefreshToken.for_user(user)
            new_refresh_str = str(new_refresh)

            response = Response(
                {
                    "access": access_str,
                    "refresh": new_refresh_str,
                    "user": UserSerializer(user).data,
                    "organisation": OrganisationSerializer(user.organisation).data,
                },
                status=status.HTTP_200_OK,
            )
            set_refresh_cookie(response, new_refresh_str)
            return response
        except TokenError:
            response = Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
            return response


class LogoutAPIView(APIView):
    """Logs out the user, blacklists any refresh token, and clears the HttpOnly cookie."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_refresh = request.data.get("refresh") or request.COOKIES.get(
            REFRESH_COOKIE_NAME
        )
        if raw_refresh:
            try:
                token = RefreshToken(raw_refresh)
                token.blacklist()
            except Exception:
                pass

        if request.user and request.user.is_authenticated:
            log_audit_event(
                organisation=request.user.organisation,
                actor=request.user,
                action="USER_LOGOUT",
                target_type="User",
                target_id=request.user.id,
                summary=f"{request.user.full_name} logged out.",
                request=request,
            )

        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
        return response


class CurrentUserProfileAPIView(APIView):
    """Retrieves or updates the currently authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "organisation": OrganisationSerializer(request.user.organisation).data,
            }
        )

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_audit_event(
            organisation=request.user.organisation,
            actor=request.user,
            action="PROFILE_UPDATED",
            target_type="User",
            target_id=request.user.id,
            summary=f"{request.user.full_name} updated their account profile.",
            request=request,
        )
        return Response(UserSerializer(request.user).data)


class ChangePasswordAPIView(APIView):
    """Allows an authenticated user to change their own password."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"current_password": ["Current password is incorrect."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password", "updated_at"])
        log_audit_event(
            organisation=request.user.organisation,
            actor=request.user,
            action="PASSWORD_CHANGED",
            target_type="User",
            target_id=request.user.id,
            summary=f"{request.user.full_name} changed their password.",
            request=request,
        )
        return Response({"detail": "Password updated successfully."})


class PasswordRecoveryRequestAPIView(APIView):
    """Generates a time-limited password reset token."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordRecoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        user = User.objects.filter(email=email, is_active=True).first()

        response_payload = {
            "detail": (
                "If an active account matches that email address, password reset "
                "instructions have been generated."
            )
        }

        if user:
            token_str = secrets.token_urlsafe(32)
            reset_obj = PasswordResetToken.objects.create(
                user=user,
                token=token_str,
                expires_at=timezone.now() + timedelta(hours=1),
            )
            log_audit_event(
                organisation=user.organisation,
                actor=user,
                action="PASSWORD_RESET_REQUESTED",
                target_type="User",
                target_id=user.id,
                summary=f"Password recovery token generated for {user.email}.",
                request=request,
            )
            email_sent = send_password_reset_email(user, reset_obj.token)
            response_payload["reset_token"] = reset_obj.token
            response_payload["email_dispatched"] = email_sent

        return Response(response_payload, status=status.HTTP_200_OK)


class TestEmailAPIView(APIView):
    """
    Authenticated administrative endpoint to test real SMTP server delivery.
    Sends a test email to the requested address and returns delivery telemetry.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        target_email = (request.data.get("recipient_email") or request.user.email).strip().lower()
        result = send_smtp_diagnostic_test(
            recipient_email=target_email,
            actor_name=request.user.full_name,
        )
        return Response(
            result,
            status=status.HTTP_200_OK if result.get("success") else status.HTTP_502_BAD_GATEWAY,
        )


class PasswordResetConfirmAPIView(APIView):
    """Validates a password reset token and sets a new password."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data["token"].strip()
        new_password = serializer.validated_data["new_password"]

        reset_obj = (
            PasswordResetToken.objects.select_related("user", "user__organisation")
            .filter(token=token_str)
            .first()
        )
        if not reset_obj or not reset_obj.is_valid():
            return Response(
                {"detail": "Invalid or expired password reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = reset_obj.user
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        reset_obj.used = True
        reset_obj.save(update_fields=["used"])

        log_audit_event(
            organisation=user.organisation,
            actor=user,
            action="PASSWORD_RESET_COMPLETED",
            target_type="User",
            target_id=user.id,
            summary=f"Password reset completed for {user.email}.",
            request=request,
        )
        return Response(
            {"detail": "Your password has been reset successfully. You may now log in."},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    Administrative CRUD for user provisioning and role assignment, plus
    Supervisor/Admin account approval and colleague directory lookup.
    """

    filterset_fields = [
        "role",
        "personnel_category",
        "approval_status",
        "is_active",
        "department",
    ]
    search_fields = ["full_name", "email", "employee_id", "department"]
    ordering_fields = ["full_name", "created_at", "role", "personnel_category"]

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.select_related("organisation").filter(
            organisation=user.organisation
        )
        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return UserCreateUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ("colleagues",):
            return [permissions.IsAuthenticated()]
        if self.action in ("approve",):
            return [IsSupervisorOrAdmin()]
        if self.action in ("list", "retrieve") and self.request.user.is_authenticated:
            if self.request.user.role in (UserRole.ADMIN, UserRole.SUPERVISOR):
                return [permissions.IsAuthenticated()]
        return [IsSystemAdmin()]

    def perform_create(self, serializer):
        new_user = serializer.save(organisation=self.request.user.organisation)
        log_audit_event(
            organisation=self.request.user.organisation,
            actor=self.request.user,
            action="USER_CREATED",
            target_type="User",
            target_id=new_user.id,
            summary=(
                f"Admin provisioned user {new_user.full_name} ({new_user.email}) "
                f"with role {new_user.role} and category {new_user.personnel_category}."
            ),
            request=self.request,
        )

    def perform_update(self, serializer):
        updated_user = serializer.save()
        log_audit_event(
            organisation=self.request.user.organisation,
            actor=self.request.user,
            action="USER_UPDATED",
            target_type="User",
            target_id=updated_user.id,
            summary=(
                f"Admin updated user {updated_user.full_name} "
                f"(role={updated_user.role}, category={updated_user.personnel_category}, active={updated_user.is_active})."
            ),
            request=self.request,
        )

    @action(detail=False, methods=["get"], url_path="colleagues")
    def colleagues(self, request):
        """Returns active, approved users in the authenticated user's organisation for shift/handover selection."""
        role_filter = request.query_params.get("role")
        category_filter = request.query_params.get("personnel_category")
        qs = User.objects.filter(
            organisation=request.user.organisation,
            is_active=True,
            approval_status=AccountApprovalStatus.APPROVED,
        ).select_related("organisation")
        if role_filter:
            qs = qs.filter(role=role_filter)
        if category_filter:
            qs = qs.filter(personnel_category=category_filter)
        serializer = UserSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """Allows a Supervisor or System Administrator to approve or reject an account registration."""
        target_user = self.get_object()
        new_status = (
            request.data.get("approval_status") or AccountApprovalStatus.APPROVED
        ).upper()
        if new_status not in (
            AccountApprovalStatus.APPROVED,
            AccountApprovalStatus.REJECTED,
            AccountApprovalStatus.PENDING,
        ):
            return Response(
                {"detail": "Invalid approval_status. Use APPROVED, REJECTED, or PENDING."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user.approval_status = new_status
        if new_status == AccountApprovalStatus.REJECTED:
            target_user.is_active = False
        elif new_status == AccountApprovalStatus.APPROVED:
            target_user.is_active = True
        target_user.save(update_fields=["approval_status", "is_active", "updated_at"])

        log_audit_event(
            organisation=request.user.organisation,
            actor=request.user,
            action="USER_APPROVAL_UPDATED",
            target_type="User",
            target_id=target_user.id,
            summary=(
                f"{request.user.full_name} ({request.user.role}) updated approval status for "
                f"{target_user.full_name} ({target_user.email}) to {new_status}."
            ),
            request=request,
        )

        Notification.objects.create(
            organisation=request.user.organisation,
            recipient=target_user,
            notification_type=NotificationType.SYSTEM,
            title=f"Account Verification Status: {new_status}",
            message=(
                f"Your ShiftSync Aviation account ({target_user.employee_id or target_user.email}) "
                f"has been marked as {new_status} by {request.user.full_name}."
            ),
        )
        return Response(UserSerializer(target_user).data)

    @action(detail=True, methods=["post"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        """Activates or deactivates a user account."""
        target_user = self.get_object()
        if target_user.id == request.user.id:
            return Response(
                {"detail": "You cannot deactivate your own administrator account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=["is_active", "updated_at"])
        state_str = "activated" if target_user.is_active else "deactivated"
        log_audit_event(
            organisation=request.user.organisation,
            actor=request.user,
            action="USER_STATUS_TOGGLED",
            target_type="User",
            target_id=target_user.id,
            summary=f"Admin {state_str} user account {target_user.full_name} ({target_user.email}).",
            request=request,
        )
        return Response(UserSerializer(target_user).data)


class CurrentOrganisationConfigAPIView(APIView):
    """Allows any authenticated user to read their organisation's config, and Admins to update it."""

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsSystemAdmin()]

    def get(self, request):
        return Response(OrganisationSerializer(request.user.organisation).data)

    def patch(self, request):
        org = request.user.organisation
        serializer = OrganisationSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_audit_event(
            organisation=org,
            actor=request.user,
            action="CONFIG_UPDATED",
            target_type="Organisation",
            target_id=org.id,
            summary=f"Admin {request.user.full_name} updated system configuration for {org.name}.",
            request=request,
        )
        return Response(serializer.data)


class AuditEventListAPIView(generics.ListAPIView):
    """Lists immutable audit events for the user's organisation (Supervisors and Admins)."""

    serializer_class = AuditEventSerializer
    permission_classes = [IsSupervisorOrAdmin]
    filterset_fields = ["action", "target_type"]
    search_fields = ["summary", "action", "target_id", "actor__full_name", "actor__email"]

    def get_queryset(self):
        return AuditEvent.objects.select_related("actor", "organisation").filter(
            organisation=self.request.user.organisation
        )
