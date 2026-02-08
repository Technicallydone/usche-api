from typing import Optional
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet

from .models import User, Role


def user_has_permission(user: User, permission_code: str) -> bool:
    """
    Return True if user has the given permission through their role.
    """

    # SUPERUSER BYPASS
    if getattr(user, "is_superuser", False):
        return True

    role: Optional[Role] = getattr(user, "role", None)
    if not role:
        return False

    return role.permissions.filter(code_name=permission_code).exists()


class HasAppPermission(permissions.BasePermission):
    """
    DRF permission class to check permissions per action.
    """

    def has_permission(self, request: Request, view: ViewSet) -> bool:
        user: User = request.user  # type: ignore

        # Safety check
        if not user or not user.is_authenticated:
            return False

        # SUPERUSER BYPASS
        if user.is_superuser:
            return True

        action: Optional[str] = getattr(view, "action", None)
        permission_mapping: dict[str, str] = getattr(view, "permission_mapping", {})

        # No action or no mapping → allow
        if not action:
            return True

        perm_code: Optional[str] = permission_mapping.get(action)
        if not perm_code:
            return True

        if not user_has_permission(user, perm_code):
            raise PermissionDenied("You do not have permission to perform this action.")

        return True
