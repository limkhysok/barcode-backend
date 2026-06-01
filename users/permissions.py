from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request


class IsBoss(BasePermission):
    """Allow access only to users with is_boss=True."""
    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_boss', False)
        )


class IsAdminOrBoss(BasePermission):
    """Permission check for Admin (staff/superuser) or Boss role."""
    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(
            request.user and
            request.user.is_authenticated and (
                getattr(request.user, 'is_staff', False) or
                getattr(request.user, 'is_superuser', False) or
                getattr(request.user, 'is_boss', False)
            )
        )


class RBACPermission(BasePermission):
    """
    Role-based access control:
      - GET / HEAD / OPTIONS (read)  → any authenticated user
      - POST (create)                → any authenticated user
      - PUT / PATCH (edit)           → boss or staff/superadmin
      - DELETE                       → superadmin only
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS or request.method == 'POST':
            return True

        if request.method in ('PUT', 'PATCH'):
            return bool(
                getattr(request.user, 'is_boss', False) or
                getattr(request.user, 'is_staff', False) or
                getattr(request.user, 'is_superuser', False)
            )

        if request.method == 'DELETE':
            return bool(getattr(request.user, 'is_superuser', False))

        return False
