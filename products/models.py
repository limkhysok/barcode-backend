from django.db import models
from django.conf import settings


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Fasteners", "Fasteners"),
        ("Accessories", "Accessories"),
    ]

    product_name = models.CharField(max_length=255, null=False, blank=False)
    category = models.CharField(
        max_length=255, choices=CATEGORY_CHOICES, default="Fasteners"
    )
    cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reorder_level = models.IntegerField(default=5)
    supplier = models.CharField(max_length=255, null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.product_name} ({self.supplier})"
