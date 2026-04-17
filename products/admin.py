from django.contrib import admin
from django.utils.html import format_html
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'row_number', 'product_thumbnail', 'barcode', 'product_name',
        'category', 'cost_per_unit', 'reorder_level', 'supplier',
        'created_by', 'created_at', 'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    search_fields = ('barcode', 'product_name', 'supplier')
    list_filter = ('category', 'created_at')

    @admin.display(description='#', ordering='id')
    def row_number(self, obj):
        return obj.id

    @admin.display(description='Picture')
    def product_thumbnail(self, obj):
        if obj.product_picture:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.product_picture.url)
        return '—'
