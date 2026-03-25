from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='productid', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'barcode', 'product_name', 'category',
            'cost_per_unit', 'reorder_level', 'supplier',
            'created_at', 'updated_at', 'created_by',
        ]
        read_only_fields = ('created_at', 'updated_at', 'created_by')
