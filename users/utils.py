from ipware import get_client_ip
from .models import UserActivity


def log_activity(request, action, details=None):
    ip, _ = get_client_ip(request)
    UserActivity.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details=details or {},
    )
