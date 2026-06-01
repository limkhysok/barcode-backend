from decimal import Decimal

from django.contrib import admin
from core.admin_site import admin_site
from .models import Transaction, TransactionItem


class TransactionItemInline(admin.TabularInline):  # type: ignore[type-arg]
    model = TransactionItem
    extra = 0
    readonly_fields = ('inventory', 'cost_per_unit', 'line_total')

    @admin.display(description='Line Total')
    def line_total(self, obj: TransactionItem) -> Decimal:
        return obj.line_total


@admin.register(Transaction, site=admin_site)
class TransactionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        'row_number', 'transaction_type', 'performed_by',
        'total_transaction_value', 'transaction_date',
    )
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('items__inventory__product__product_name',)
    readonly_fields = ('transaction_date', 'performed_by')
    inlines = [TransactionItemInline]  # type: ignore[type-arg]

    @admin.display(description='#', ordering='id')
    def row_number(self, obj: Transaction) -> int:
        return obj.id


@admin.register(TransactionItem, site=admin_site)
class TransactionItemAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        'row_number', 'transaction', 'inventory',
        'quantity', 'cost_per_unit', 'line_total',
    )
    list_filter = ('transaction__transaction_type',)
    search_fields = (
        'inventory__product__product_name',
        'transaction__id',
    )
    readonly_fields = ('transaction', 'inventory', 'cost_per_unit', 'line_total')

    @admin.display(description='#', ordering='id')
    def row_number(self, obj: TransactionItem) -> int:
        return obj.id  # type: ignore[return-value]

    @admin.display(description='Line Total')
    def line_total(self, obj: TransactionItem) -> Decimal:
        return obj.line_total
