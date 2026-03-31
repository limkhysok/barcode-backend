from rest_framework import serializers
from .models import Inventory
from products.serializers import ProductSerializer

class InventorySerializer(serializers.ModelSerializer):
    # Related Product information for display
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'product_details',
            'site', 'location', 'quantity_on_hand', 
            'stock_value', 'reorder_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'stock_value', 'reorder_status', 'created_at', 'updated_at']
