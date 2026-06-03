from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction as db_transaction
from rest_framework import serializers

from .models import Transaction, TransactionItem
from inventory.models import Inventory


class TransactionItemSerializer(serializers.ModelSerializer[TransactionItem]):
    product_name = serializers.CharField(source='inventory.product.product_name', read_only=True)
    barcode = serializers.CharField(source='inventory.product.barcode', read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = TransactionItem
        fields = ['id', 'inventory', 'product_name', 'barcode', 'quantity', 'cost_per_unit', 'line_total']
        read_only_fields = ['cost_per_unit', 'line_total']

    def get_line_total(self, obj: TransactionItem) -> Decimal:
        return obj.line_total


class TransactionSerializer(serializers.ModelSerializer[Transaction]):
    items = TransactionItemSerializer(many=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)
    total_transaction_value = serializers.SerializerMethodField()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Transaction
        fields = [
            'id', 'transaction_type',
            'performed_by', 'performed_by_username',
            'total_transaction_value',
            'items',
            'transaction_date',
        ]
        read_only_fields = ['performed_by', 'transaction_date']

    def get_total_transaction_value(self, obj: Transaction) -> Decimal:
        return obj.total_transaction_value

    def _validate_item_structure(
        self,
        transaction_type: str,
        item: dict[str, Any],
        index: int,
    ) -> dict[str, Any] | None:
        """Validate quantity sign only. Stock level and cost checks happen inside the atomic block."""
        quantity: int = item.get('quantity', 0)

        if transaction_type == 'Sale':
            if quantity >= 0:
                return {'item': index, 'quantity': 'Sale quantities must be negative.'}

        elif transaction_type == 'Receive' and quantity <= 0:
            return {'item': index, 'quantity': 'Receive quantities must be positive.'}

        return None

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        transaction_type: str | None = attrs.get('transaction_type')
        items: list[dict[str, Any]] = attrs.get('items', [])

        if not items:
            raise serializers.ValidationError({'items': 'At least one item is required.'})

        if transaction_type not in ['Receive', 'Sale']:
            raise serializers.ValidationError({'transaction_type': 'Must be Receive or Sale.'})

        item_errors: list[dict[str, Any]] = [
            error
            for i, item in enumerate(items)
            if (error := self._validate_item_structure(transaction_type, item, i + 1))
        ]

        if item_errors:
            raise serializers.ValidationError({'items': item_errors})

        return attrs

    def _check_stock_and_cost(
        self,
        transaction_type: str,
        items_data: list[dict[str, Any]],
        locked_inventory: dict[int, Inventory],
    ) -> list[dict[str, Any]]:
        """
        Validate stock levels and product cost after acquiring DB locks.
        Must be called inside an atomic block with select_for_update() already applied.
        Returns a list of error dicts, or an empty list if all items are valid.
        """
        errors: list[dict[str, Any]] = []
        for i, item_data in enumerate(items_data):
            inventory: Inventory = locked_inventory[item_data['inventory'].id]
            quantity: int = item_data['quantity']
            cost_per_unit = inventory.product.cost_per_unit

            if not cost_per_unit:
                errors.append({
                    'item': i + 1,
                    'detail': (
                        f'Product "{inventory.product.product_name}" has no cost set. '
                        'Set a cost_per_unit on the product before creating transactions.'
                    ),
                })
                continue

            if transaction_type == 'Sale' and abs(quantity) > inventory.quantity_on_hand:
                errors.append({
                    'item': i + 1,
                    'quantity': (
                        f'Insufficient stock. '
                        f'Current balance is only {inventory.quantity_on_hand} units.'
                    ),
                })

        return errors

    def create(self, validated_data: dict[str, Any]) -> Transaction:
        request = self.context.get('request')
        items_data: list[dict[str, Any]] = validated_data.pop('items')

        if request and request.user.is_authenticated:
            validated_data['performed_by'] = request.user

        with db_transaction.atomic():
            transaction = Transaction.objects.create(**validated_data)

            inventory_ids: list[int] = [item['inventory'].id for item in items_data]
            locked_inventory: dict[int, Inventory] = {
                inv.id: inv
                for inv in Inventory.objects.select_for_update()
                                            .select_related('product')
                                            .filter(id__in=inventory_ids)
            }

            errors = self._check_stock_and_cost(
                validated_data['transaction_type'], items_data, locked_inventory
            )
            if errors:
                raise serializers.ValidationError({'items': errors})

            for item_data in items_data:
                inventory = locked_inventory[item_data['inventory'].id]
                quantity: int = item_data['quantity']
                cost_per_unit = inventory.product.cost_per_unit

                TransactionItem.objects.create(
                    transaction=transaction,
                    inventory=inventory,
                    quantity=quantity,
                    cost_per_unit=cost_per_unit,
                )

                inventory.quantity_on_hand += quantity
                inventory.refresh_stats()

        return transaction

    def update(self, instance: Transaction, validated_data: dict[str, Any]) -> Transaction:
        items_data: list[dict[str, Any]] | None = validated_data.pop('items', None)

        with db_transaction.atomic():
            instance.transaction_type = validated_data.get('transaction_type', instance.transaction_type)
            instance.save()

            if items_data is not None:
                existing_inventory_ids: list[int] = list(
                    TransactionItem.objects.filter(transaction=instance)
                    .values_list('inventory_id', flat=True)
                )
                new_inventory_ids: list[int] = [item['inventory'].id for item in items_data]
                all_ids = list(set(existing_inventory_ids + new_inventory_ids))
                locked_inventory: dict[int, Inventory] = {
                    inv.id: inv
                    for inv in Inventory.objects.select_for_update()
                                                .select_related('product')
                                                .filter(id__in=all_ids)
                }

                for existing_item in TransactionItem.objects.filter(transaction=instance):
                    inventory = locked_inventory[existing_item.inventory_id]  # type: ignore[attr-defined]
                    inventory.quantity_on_hand -= existing_item.quantity
                    inventory.refresh_stats()

                errors = self._check_stock_and_cost(
                    instance.transaction_type, items_data, locked_inventory
                )
                if errors:
                    raise serializers.ValidationError({'items': errors})

                TransactionItem.objects.filter(transaction=instance).delete()

                for item_data in items_data:
                    inventory = locked_inventory[item_data['inventory'].id]
                    quantity = item_data['quantity']
                    cost_per_unit = inventory.product.cost_per_unit

                    TransactionItem.objects.create(
                        transaction=instance,
                        inventory=inventory,
                        quantity=quantity,
                        cost_per_unit=cost_per_unit,
                    )

                    inventory.quantity_on_hand += quantity
                    inventory.refresh_stats()

        return instance
