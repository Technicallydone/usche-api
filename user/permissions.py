from typing import Optional, Union, List

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet

from .models import User, Role


# -----------------------------
# TYPE
# -----------------------------
PermissionType = Union[str, List[str]]


# -----------------------------
# CORE CHECKER
# -----------------------------
def user_has_permission(user: User, permission_codes: PermissionType) -> bool:
    """
    Return True if user has ANY of the given permissions.
    Supports:
    - single permission string
    - list of permissions (OR logic)
    """

    # SUPERUSER BYPASS
    if getattr(user, "is_superuser", False):
        return True

    role: Optional[Role] = getattr(user, "role", None)
    if not role:
        return False

    # normalize to list
    if isinstance(permission_codes, str):
        permission_codes = [permission_codes]

    return role.permissions.filter(
        code_name__in=permission_codes
    ).exists()


# -----------------------------
# DRF PERMISSION CLASS
# -----------------------------
class HasAppPermission(permissions.BasePermission):
    """
    DRF permission class supporting multiple permissions per action.
    """

    def has_permission(self, request: Request, view: ViewSet) -> bool:
        action: Optional[str] = getattr(view, "action", None)

        permission_mapping: dict[str, Optional[PermissionType]] = getattr(
            view,
            "permission_mapping",
            {},
        )

        if not action:
            return True

        perm_code: Optional[PermissionType] = permission_mapping.get(action)

        if not perm_code:
            return True

        user: Optional[User] = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return False

        # SUPERUSER BYPASS
        if getattr(user, "is_superuser", False):
            return True

        # CHECK PERMISSION
        if not user_has_permission(user, perm_code):
            raise PermissionDenied(
                "You do not have permission to perform this action."
            )

        return True