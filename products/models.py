from django.db import models
from django.conf import settings

class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Fasteners", "Fasteners"),
        ("Accessories", "Accessories"),
    ]

    barcode = models.CharField(
        max_length=20,
        unique=True,
        db_collation='utf8mb4_bin',
        help_text="Physical barcode scanned from the product. Must be unique."
    )
    product_name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=255, choices=CATEGORY_CHOICES, default="Fasteners"
    )
    # Using DecimalField is correct for currency—never use FloatField!
    cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reorder_level = models.PositiveIntegerField(default=5) # Added PositiveIntegerField
    supplier = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-id']

    def __str__(self):
        # Fixed self.productid -> self.id
        return f"#{self.id} - {self.product_name} ({self.barcode})"