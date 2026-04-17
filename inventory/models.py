from django.core.validators import MinValueValidator
from django.db import models
from products.models import Product


STATUS_LOW = "LOW"
STATUS_NO = "No"
STATUS_NO_STOCK = "NO STOCK"

REORDER_CHOICES = [(STATUS_LOW, STATUS_LOW), (STATUS_NO, STATUS_NO), (STATUS_NO_STOCK, STATUS_NO_STOCK)]


class Inventory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="inventory_records"
    )
    site = models.CharField(max_length=255, db_index=True)  # Store A, B, C
    location = models.CharField(max_length=255)
    quantity_on_hand = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    stock_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reorder_status = models.CharField(
        max_length=8, choices=REORDER_CHOICES, default=STATUS_NO, db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory"
        unique_together = [["product", "site", "location"]]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_on_hand__gte=0),
                name='quantity_on_hand_non_negative',
            )
        ]

    def __str__(self):
        return f"{self.product.product_name} at {self.site} ({self.location})"

    def refresh_stats(self):
        """Recalculate stock value and reorder status based on quantity."""
        from decimal import Decimal
        cost = self.product.cost_per_unit or Decimal('0.00')
        self.stock_value = self.quantity_on_hand * cost
        if self.quantity_on_hand == 0:
            self.reorder_status = STATUS_NO_STOCK
        elif self.quantity_on_hand <= self.product.reorder_level:
            self.reorder_status = STATUS_LOW
        else:
            self.reorder_status = STATUS_NO
        self.save(update_fields=['quantity_on_hand', 'stock_value', 'reorder_status'])
