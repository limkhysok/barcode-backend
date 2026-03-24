from django.db import models
from products.models import Product


class Inventory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="inventory_records"
    )
    site = models.CharField(max_length=255)  # Store A,B,C
    location = models.CharField(max_length=255)
    order_date = models.DateField(null=True, blank=True)
    product_description = models.CharField(max_length=255)
    quantity_on_hand = models.IntegerField(default=0)
    stock_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reorder_status = models.CharField(max_length=255, default="No")  # yes and no

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory"

    def __str__(self):
        return f"{self.product.product_name} at {self.site} ({self.location})"
