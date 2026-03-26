from rest_framework import serializers
from .models import Transaction
from inventory.serializers import InventorySerializer

class TransactionSerializer(serializers.ModelSerializer):
    inventory_details = InventorySerializer(source='inventory', read_only=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)

    # Flat convenience fields so the frontend doesn't have to dig into inventory_details
    product_name = serializers.CharField(source='inventory.product.product_name', read_only=True)
    barcode = serializers.CharField(source='inventory.product.barcode', read_only=True)
    site = serializers.CharField(source='inventory.site', read_only=True)
    location = serializers.CharField(source='inventory.location', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'inventory', 'inventory_details',
            'product_name', 'barcode', 'site', 'location',
            'transaction_type', 'quantity', 'total_value',
            'performed_by', 'performed_by_username',
            'transaction_date',
        ]
        read_only_fields = ['performed_by', 'transaction_date', 'total_value']

    def validate(self, data):
        """ Check that sale quantity does not exceed current stock """
        inventory = data.get('inventory')
        transaction_type = data.get('transaction_type')
        quantity = data.get('quantity', 0)

        # If it's a Sale, it must be negative or zero (according to your signed logic)
        # and it cannot exceed the existing quantity_on_hand.
        if transaction_type == "Sale":
            if quantity > 0:
                 raise serializers.ValidationError({"quantity": "Sales must be recorded as negative numbers."})
            
            # Use abs() to check if we are selling more than we have
            if abs(quantity) > inventory.quantity_on_hand:
                raise serializers.ValidationError(
                    {"quantity": f"Insufficient stock. Current balance is only {inventory.quantity_on_hand} units."}
                )
        
        elif transaction_type == "Receive" and quantity < 0:
             raise serializers.ValidationError({"quantity": "Receives must be recorded as positive numbers."})

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['performed_by'] = request.user

        # Auto-calculate total_value = |quantity| x cost_per_unit
        from decimal import Decimal
        inventory = validated_data['inventory']
        cost = inventory.product.cost_per_unit or Decimal('0.00')
        validated_data['total_value'] = abs(validated_data['quantity']) * cost

        transaction = super().create(validated_data)
        
        # Update Inventory stock based on transaction
        inventory = transaction.inventory
        # Using the signed quantity directly (Positive means Receive, Negative means Sale)
        # This simplifies the math!
        inventory.quantity_on_hand += transaction.quantity
        
        inventory.refresh_stats()
        return transaction
