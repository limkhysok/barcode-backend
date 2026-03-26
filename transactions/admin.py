from django.contrib import admin
from .models import Transaction, TransactionItem


class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ('cost_per_unit', 'line_total')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'performed_by', 'total_transaction_value', 'transaction_date')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('items__inventory__product__product_name',)
    readonly_fields = ('transaction_date',)
    inlines = [TransactionItemInline]
