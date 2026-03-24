from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_type', 'inventory', 'quantity', 
        'performed_by', 'transaction_date'
    )
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('inventory__product__product_name', 'notes')
    readonly_fields = ('transaction_date',)
