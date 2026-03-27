from decimal import Decimal
from rest_framework import serializers
from .models import Transaction, TransactionItem


class TransactionItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='inventory.product.product_name', read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = TransactionItem
        fields = ['id', 'inventory', 'product_name', 'quantity', 'cost_per_unit', 'line_total']
        read_only_fields = ['cost_per_unit', 'line_total']

    def get_line_total(self, obj):
        return obj.line_total


class TransactionSerializer(serializers.ModelSerializer):
    items = TransactionItemSerializer(many=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)
    total_transaction_value = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type',
            'performed_by', 'performed_by_username',
            'total_transaction_value',
            'items',
            'transaction_date',
        ]
        read_only_fields = ['performed_by', 'transaction_date']

    def get_total_transaction_value(self, obj):
        return obj.total_transaction_value

    def _validate_item(self, transaction_type, item, index):
        quantity = item.get('quantity', 0)
        inventory = item.get('inventory')

        if transaction_type == 'Sale':
            if quantity >= 0:
                return {'item': index, 'quantity': 'Sale quantities must be negative.'}
            if abs(quantity) > inventory.quantity_on_hand:
                return {'item': index, 'quantity': f'Insufficient stock. Current balance is only {inventory.quantity_on_hand} units.'}

        elif transaction_type == 'Receive' and quantity <= 0:
            return {'item': index, 'quantity': 'Receive quantities must be positive.'}

        return None

    def validate(self, data):
        transaction_type = data.get('transaction_type')
        items = data.get('items', [])

        if not items:
            raise serializers.ValidationError({'items': 'At least one item is required.'})

        if transaction_type not in ['Receive', 'Sale']:
            raise serializers.ValidationError({'transaction_type': 'Must be Receive or Sale.'})

        item_errors = [
            error for i, item in enumerate(items)
            if (error := self._validate_item(transaction_type, item, i + 1))
        ]

        if item_errors:
            raise serializers.ValidationError({'items': item_errors})

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        items_data = validated_data.pop('items')

        if request and request.user.is_authenticated:
            validated_data['performed_by'] = request.user

        transaction = Transaction.objects.create(**validated_data)

        for item_data in items_data:
            inventory = item_data['inventory']
            quantity = item_data['quantity']
            cost_per_unit = inventory.product.cost_per_unit or Decimal('0.00')

            TransactionItem.objects.create(
                transaction=transaction,
                inventory=inventory,
                quantity=quantity,
                cost_per_unit=cost_per_unit,
            )

            # Update inventory stock and recalculate stats
            inventory.quantity_on_hand += quantity
            inventory.refresh_stats()

        return transaction

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update top-level fields
        instance.transaction_type = validated_data.get('transaction_type', instance.transaction_type)
        instance.save()

        if items_data is not None:
            # Reverse inventory effects of all existing items
            for existing_item in instance.items.all():
                inventory = existing_item.inventory
                inventory.quantity_on_hand -= existing_item.quantity
                inventory.refresh_stats()

            # Delete all existing items
            instance.items.all().delete()

            # Recreate items and apply new inventory effects
            for item_data in items_data:
                inventory = item_data['inventory']
                quantity = item_data['quantity']
                cost_per_unit = inventory.product.cost_per_unit or Decimal('0.00')

                TransactionItem.objects.create(
                    transaction=instance,
                    inventory=inventory,
                    quantity=quantity,
                    cost_per_unit=cost_per_unit,
                )

                inventory.quantity_on_hand += quantity
                inventory.refresh_stats()

        return instance
