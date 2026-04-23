from django.db import models
from django.db.models import Q
from django.conf import settings

class Transaction(models.Model):
    TRANSACTION_TYPES = [('Receive', 'Receive'), ('Sale', 'Sale')]

    # The "Envelope" (Header)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True, db_index=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-transaction_date', '-id']
        constraints = [
            models.CheckConstraint(
                condition=Q(transaction_type__in=['Receive', 'Sale']),
                name='transaction_type_valid',
            )
        ]

    @property
    def total_transaction_value(self):
        # Dynamically calculate total from all items
        return sum(item.line_total for item in self.items.all())

class TransactionItem(models.Model):
    # The "Contents" (Details)
    transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)
    inventory = models.ForeignKey('inventory.Inventory', on_delete=models.PROTECT)

    # Snapshot fields (Keep these to record the price/name AT THE TIME of transaction)
    quantity = models.IntegerField()
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

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
    def line_total(self):
        if self.quantity is None or self.cost_per_unit is None:
            return 0
        return self.quantity * self.cost_per_unit