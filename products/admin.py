from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'barcode', 'product_name', 'category', 'cost_per_unit', 
        'reorder_level', 'supplier', 'created_at'
    )
    search_fields = ('barcode', 'product_name', 'supplier')
    list_filter = ('category', 'created_at')
