from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Add any additional fields here if needed
    name = models.CharField(max_length=255, blank=True)
    is_boss = models.BooleanField(default=False)
    # is_staff is already included in AbstractUser

    def __str__(self):
        return self.username
