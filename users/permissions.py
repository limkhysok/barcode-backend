from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrBoss(BasePermission):
    """
    Permission check for Admin (staff/superuser) or Boss role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and (
                request.user.is_staff or 
                request.user.is_superuser or 
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

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS or request.method == 'POST':
            return True

        if request.method in ('PUT', 'PATCH'):
            return (
                request.user.is_boss or 
                request.user.is_staff or 
                request.user.is_superuser
            )

        if request.method == 'DELETE':
            return request.user.is_superuser

        return False
