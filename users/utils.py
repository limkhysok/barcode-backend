from __future__ import annotations

from rest_framework.request import Request
from ipware import get_client_ip  # type: ignore[import-untyped]
from .models import UserActivity


def log_activity(request: Request, action: str, details: dict[str, object] | None = None) -> None:
    ip, _ = get_client_ip(request)
    UserActivity.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details=details or {},
    )
