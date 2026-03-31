from django.core.validators import MinValueValidator
from django.db import models
from products.models import Product


REORDER_CHOICES = [("Yes", "Yes"), ("No", "No")]


class Inventory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="inventory_records"
    )
    site = models.CharField(max_length=255)  # Store A, B, C
    location = models.CharField(max_length=255)
    quantity_on_hand = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    stock_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reorder_status = models.CharField(
        max_length=3, choices=REORDER_CHOICES, default="No"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory"
        unique_together = [["product", "site", "location"]]

    def __str__(self):
        return f"{self.product.product_name} at {self.site} ({self.location})"

    def refresh_stats(self):
        """Recalculate stock value and reorder status based on quantity."""
        from decimal import Decimal
        cost = self.product.cost_per_unit or Decimal('0.00')
        self.stock_value = self.quantity_on_hand * cost
        self.reorder_status = "Yes" if self.quantity_on_hand <= self.product.reorder_level else "No"
        self.save(update_fields=['quantity_on_hand', 'stock_value', 'reorder_status'])
