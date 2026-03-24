from rest_framework import serializers
from .models import Inventory
from products.serializers import ProductSerializer

class InventorySerializer(serializers.ModelSerializer):
    # Related Product information for display
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'product_details', 'product_description',
            'site', 'location', 'quantity_on_hand', 
            'stock_value', 'reorder_status', 'order_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
