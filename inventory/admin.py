from django.contrib import admin
from .models import Inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'product_description', 'site', 'location', 
        'quantity_on_hand', 'stock_value', 'reorder_status', 'order_date'
    )
    list_filter = ('site', 'reorder_status', 'order_date')
    search_fields = ('product__product_name', 'product_description', 'site', 'location')
    date_hierarchy = 'order_date'
