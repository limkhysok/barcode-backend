from __future__ import annotations

from typing import Any

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest
from axes.signals import user_locked_out  # type: ignore[import-untyped]
from ipware import get_client_ip  # type: ignore[import-untyped]
from .models import UserActivity


def _get_ua(request: HttpRequest | None) -> str:
    return request.META.get('HTTP_USER_AGENT', '') if request else ''


@receiver(user_logged_in)
def on_user_login(sender: type[Any], request: HttpRequest, user: Any, **_kwargs: Any) -> None:
    ip, _ = get_client_ip(request)
    UserActivity.objects.create(
        user=user,
        action='login',
        ip_address=ip,
        user_agent=_get_ua(request),
    )


@receiver(user_logged_out)
def on_user_logout(sender: type[Any], request: HttpRequest, user: Any, **_kwargs: Any) -> None:
    if user:
        ip, _ = get_client_ip(request)
        UserActivity.objects.create(
            user=user,
            action='logout',
            ip_address=ip,
            user_agent=_get_ua(request),
        )


@receiver(user_locked_out)
def on_user_locked_out(sender: type[Any], request: HttpRequest, username: str, ip_address: str, **_kwargs: Any) -> None:
    ip, _ = get_client_ip(request)
    UserActivity.objects.create(
        user=None,
        action='login_failed',
        ip_address=ip,
        user_agent=_get_ua(request),
        details={'username': username, 'locked_out': True},
    )
