from rest_framework import serializers
from .models import Transaction
from inventory.serializers import InventorySerializer

class TransactionSerializer(serializers.ModelSerializer):
    inventory_details = InventorySerializer(source='inventory', read_only=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'inventory', 'inventory_details', 'transaction_type', 
            'quantity', 'performed_by', 'performed_by_username', 
            'transaction_date'
        ]
        read_only_fields = ['performed_by', 'transaction_date']

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
        # Automatically assign the request user if not provided in validated_data
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['performed_by'] = request.user
            
        transaction = super().create(validated_data)
        
        # Update Inventory stock based on transaction
        inventory = transaction.inventory
        # Using the signed quantity directly (Positive means Receive, Negative means Sale)
        # This simplifies the math!
        inventory.quantity_on_hand += transaction.quantity
        
        inventory.refresh_stats()
        return transaction
