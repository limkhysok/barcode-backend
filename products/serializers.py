from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    barcode = serializers.CharField(
        max_length=20,
        help_text="Physical barcode scanned from the product. Must be unique. Cannot be changed after creation."
    )

    class Meta:
        model = Product
        fields = [
            'id', 'barcode', 'product_name', 'category',
            'cost_per_unit', 'reorder_level', 'supplier',
            'product_picture', 'created_at', 'updated_at', 'created_by',
        ]
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def update(self, instance, validated_data):
        validated_data.pop('barcode', None)
        return super().update(instance, validated_data)
