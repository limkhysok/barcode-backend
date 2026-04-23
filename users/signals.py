from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from axes.signals import user_locked_out
from ipware import get_client_ip
from .models import UserActivity


def _get_ua(request):
    return request.META.get('HTTP_USER_AGENT', '') if request else ''


@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    ip, _ = get_client_ip(request)
    UserActivity.objects.create(
        user=user,
        action='login',
        ip_address=ip,
        user_agent=_get_ua(request),
    )


@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    if user:
        ip, _ = get_client_ip(request)
        UserActivity.objects.create(
            user=user,
            action='logout',
            ip_address=ip,
            user_agent=_get_ua(request),
        )


@receiver(user_locked_out)
def on_user_locked_out(sender, request, username, ip_address, **kwargs):
    ip, _ = get_client_ip(request)
    UserActivity.objects.create(
        user=None,
        action='login_failed',
        ip_address=ip,
        user_agent=_get_ua(request),
        details={'username': username, 'locked_out': True},
    )
