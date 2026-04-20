from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import UserActivityLog


def _get_ip(request):
    if request is None:
        return None
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    UserActivityLog.objects.create(
        user=user,
        action='login',
        ip_address=_get_ip(request),
    )


@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    if user:
        UserActivityLog.objects.create(
            user=user,
            action='logout',
            ip_address=_get_ip(request),
        )
