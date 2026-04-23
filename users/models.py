from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    name = models.CharField(max_length=255, blank=True)
    is_boss = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class UserActivity(models.Model):
    ACTION_CHOICES = [
        # Auth
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Login Failed'),
        ('register', 'Register'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        # Products
        ('product_created', 'Product Created'),
        ('product_updated', 'Product Updated'),
        ('product_deleted', 'Product Deleted'),
        # Inventory
        ('inventory_created', 'Inventory Created'),
        ('inventory_updated', 'Inventory Updated'),
        ('inventory_deleted', 'Inventory Deleted'),
        # Transactions
        ('transaction_created', 'Transaction Created'),
        ('transaction_deleted', 'Transaction Deleted'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'

    def __str__(self):
        username = self.user.username if self.user else 'anonymous'
        return f'{username} — {self.action} at {self.timestamp:%Y-%m-%d %H:%M}'
