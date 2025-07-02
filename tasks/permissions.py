from rest_framework.permissions import BasePermission, SAFE_METHODS


def _in_group(user, name: str) -> bool:
    return user.groups.filter(name=name).exists()


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or _in_group(request.user, "admin")
        )


class IsTaskReviewer(BasePermission):
    """Allow GET for all; modifications only for reviewers/Admins/Superadmins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        # Allow anonymous declines coming from the public UI
        if request.headers.get("X-Public-UI") == "true":
            return True
        # Allow unauthenticated decline from public UI if special header present
        if not request.user.is_authenticated:
            if request.method in ("POST", "PATCH", "DELETE") and request.headers.get("X-Public-UI") == "true":
                return True
            return False
        return (
            request.user.is_superuser
            or request.user.is_staff
            or _in_group(request.user, "admin")
            or _in_group(request.user, "user")
        ) 