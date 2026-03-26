from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer
from products.models import Product
from inventory.models import Inventory
from inventory.serializers import InventorySerializer


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

    @action(detail=False, methods=['post'], url_path='scan')
    def scan(self, request):
        """
        Create a transaction by scanning a product barcode.
        POST /api/transactions/scan
        Body: { barcode, transaction_type, quantity, inventory_id (optional) }
        """
        barcode = request.data.get('barcode')
        transaction_type = request.data.get('transaction_type')
        quantity = request.data.get('quantity')
        inventory_id = request.data.get('inventory_id')

        # Validate required fields
        required = 'This field is required.'
        errors = {}
        if not barcode:
            errors['barcode'] = required
        if not transaction_type:
            errors['transaction_type'] = required
        if quantity is None:
            errors['quantity'] = required
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Find product by barcode
        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'No product found with this barcode.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 2: Find inventory records for this product
        inventory_qs = Inventory.objects.filter(product=product)
        if not inventory_qs.exists():
            return Response(
                {'detail': 'Product found but has no inventory record.', 'product': product.product_name},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Resolve which inventory record to use
        if inventory_id:
            try:
                inventory = inventory_qs.get(id=inventory_id)
            except Inventory.DoesNotExist:
                return Response(
                    {'detail': 'The specified inventory_id does not belong to this product.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif inventory_qs.count() == 1:
            inventory = inventory_qs.first()
        else:
            # Multiple records — ask frontend to specify
            return Response(
                {
                    'detail': 'Multiple inventory records found for this product. Please specify inventory_id.',
                    'inventory': InventorySerializer(inventory_qs, many=True).data,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 4: Delegate to TransactionSerializer (reuses all validation + total_value logic)
        serializer = TransactionSerializer(
            data={
                'inventory': inventory.id,
                'transaction_type': transaction_type,
                'quantity': quantity,
            },
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
