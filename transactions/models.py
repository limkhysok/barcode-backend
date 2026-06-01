from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Q
from django.conf import settings

if TYPE_CHECKING:
    from inventory.models import Inventory as InventoryModel
    from django.contrib.auth.base_user import AbstractBaseUser


class Transaction(models.Model):
    id: int
    TRANSACTION_TYPES = [('Receive', 'Receive'), ('Sale', 'Sale')]

    transaction_type: str = models.CharField(max_length=10, choices=TRANSACTION_TYPES)  # type: ignore[assignment]
    transaction_date: datetime = models.DateTimeField(auto_now_add=True, db_index=True)  # type: ignore[assignment]
    performed_by: AbstractBaseUser | None = models.ForeignKey(  # type: ignore[assignment]
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        ordering = ['-transaction_date', '-id']
        constraints = [
            models.CheckConstraint(
                condition=Q(transaction_type__in=['Receive', 'Sale']),
                name='transaction_type_valid',
            )
        ]

    @property
    def total_transaction_value(self) -> Decimal:
        return sum(
            (item.line_total for item in TransactionItem.objects.filter(transaction=self)),
            Decimal(0),
        )


class TransactionItem(models.Model):
    id: int
    transaction: Transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)  # type: ignore[assignment]
    inventory: InventoryModel = models.ForeignKey('inventory.Inventory', on_delete=models.PROTECT)  # type: ignore[assignment]

    quantity: int = models.IntegerField()  # type: ignore[assignment]
    cost_per_unit: Decimal = models.DecimalField(max_digits=10, decimal_places=2)  # type: ignore[assignment]

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(quantity=0),
                name='transaction_item_quantity_nonzero',
            ),
            models.CheckConstraint(
                condition=Q(cost_per_unit__gt=0),
                name='transaction_item_cost_positive',
            ),
        ]

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.cost_per_unit
