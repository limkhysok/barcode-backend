from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    name = models.CharField(max_length=255, blank=True)
    is_boss = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class UserActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('register', 'Register'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'

    def __str__(self):
        return f'{self.user.username} — {self.action} at {self.timestamp:%Y-%m-%d %H:%M}'
