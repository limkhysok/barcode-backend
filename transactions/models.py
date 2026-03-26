from django.db import models
from django.conf import settings

class Transaction(models.Model):
    # The "Envelope" (Header)
    transaction_type = models.CharField(max_length=10) # Receive / Sale
    transaction_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
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
    
    @property
    def line_total(self):
        return self.quantity * self.cost_per_unit