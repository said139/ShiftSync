from rest_framework import permissions
from .models import UserRole


class IsSystemAdmin(permissions.BasePermission):
    """Allows access strictly to System Administrators."""

    message = "Only System Administrators are authorised to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role == UserRole.ADMIN
        )


class IsSupervisorOrAdmin(permissions.BasePermission):
    """Allows access to Supervisors and System Administrators."""

    message = "Only Supervisors or System Administrators may access supervisory resources."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role in (UserRole.SUPERVISOR, UserRole.ADMIN)
        )


class IsSupervisorReadOnlyOrAdmin(permissions.BasePermission):
    """Supervisors have read access within their scope; Admins have full access."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.user.role == UserRole.ADMIN:
            return True
        if request.user.role == UserRole.SUPERVISOR and request.method in permissions.SAFE_METHODS:
            return True
        return False


class IsOutgoingOrAdmin(permissions.BasePermission):
    """Allows authorised operational aviation personnel (Outgoing/Incoming Crew & Admins) to create/submit handover reports."""

    message = "Only authorised operational personnel or Administrators can create or submit handover reports."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role in (
                UserRole.OUTGOING_WORKER,
                UserRole.INCOMING_WORKER,
                UserRole.ADMIN,
            )
        )


class IsSameOrganisation(permissions.BasePermission):
    """Enforces strict organisation-level data isolation across objects."""

    message = "Access denied: record belongs to another organisation."

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        obj_org_id = getattr(obj, "organisation_id", None)
        if obj_org_id is None and hasattr(obj, "id") and obj.__class__.__name__ == "Organisation":
            obj_org_id = obj.id
        return obj_org_id == request.user.organisation_id
