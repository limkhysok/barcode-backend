from django.contrib import admin
from .models import Inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'row_number', 'product', 'site', 'location',
        'quantity_on_hand', 'stock_value', 'reorder_status',
        'created_at', 'updated_at',
    )
    readonly_fields = ('stock_value', 'reorder_status', 'created_at', 'updated_at')
    list_filter = ('site', 'reorder_status')
    search_fields = ('product__product_name', 'site', 'location')

    @admin.display(description='#', ordering='id')
    def row_number(self, obj):
        return obj.id
