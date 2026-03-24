from django.db import models
from django.conf import settings
from inventory.models import Inventory


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("Receive", "Receive"),
        ("Sale", "Sale"),
    ]

    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name="transactions"
    )
    quantity = models.IntegerField()  # positive for receive, negative for sale
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date"]

    def __str__(self):
        return f"{self.transaction_type} - {self.inventory.product.product_name} ({self.quantity})"
