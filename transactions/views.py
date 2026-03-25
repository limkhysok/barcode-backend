from rest_framework import viewsets, permissions
from .models import Transaction
from .serializers import TransactionSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    """
    Log and manage stock transactions (In, Out, Adjust).
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        inventory_id = self.request.query_params.get('inventory_id')
        transaction_type = self.request.query_params.get('type')
        barcode = self.request.query_params.get('barcode')
        search = self.request.query_params.get('search')

        if inventory_id:
            queryset = queryset.filter(inventory_id=inventory_id)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if barcode:
            queryset = queryset.filter(inventory__product__barcode=barcode)
        if search:
            queryset = queryset.filter(inventory__product__product_name__icontains=search)

        return queryset
