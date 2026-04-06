from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField, Q
from django.db.models.functions import Abs
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction, TransactionItem
from .serializers import TransactionSerializer
from products.models import Product
from inventory.models import Inventory
from inventory.serializers import InventorySerializer


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Log and manage stock transactions (Receive / Sale).
    Each transaction has a single type and can contain multiple items.
    """
    queryset = Transaction.objects.prefetch_related('items__inventory__product').all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        transaction_type = self.request.query_params.get('type')
        barcode = self.request.query_params.get('barcode')
        search = self.request.query_params.get('search')

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if barcode:
            queryset = queryset.filter(items__inventory__product__barcode=barcode)
        if search:
            queryset = queryset.filter(items__inventory__product__product_name__icontains=search)

        return queryset.distinct()

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /api/v1/transactions/stats
        Returns aggregate overview — not paginated.
        """
        today = timezone.now().date()

        by_type = (
            Transaction.objects.values('transaction_type')
            .annotate(
                total_count=Count('id'),
                today_count=Count('id', filter=Q(transaction_date__date=today)),
            )
            .order_by('transaction_type')
        )

        by_type_result = {
            row['transaction_type']: {
                "total_count": row['total_count'],
                "today_count": row['today_count'],
            }
            for row in by_type
        }

        return Response({
            "total_transactions": Transaction.objects.count(),
            "today_transactions": Transaction.objects.filter(transaction_date__date=today).count(),
            "by_type": by_type_result,
        })

    @action(detail=False, methods=['post'], url_path='scan')
    def scan(self, request):
        """
        Create a single-item transaction by scanning a product barcode.
        POST /api/transactions/scan
        Body: { barcode, transaction_type, quantity, inventory_id (optional) }
        """
        barcode = request.data.get('barcode')
        transaction_type = request.data.get('transaction_type')
        quantity = request.data.get('quantity')
        inventory_id = request.data.get('inventory_id')

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
            return Response(
                {
                    'detail': 'Multiple inventory records found. Please specify inventory_id.',
                    'inventory': InventorySerializer(inventory_qs, many=True).data,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 4: Delegate to TransactionSerializer (reuses all validation logic)
        serializer = TransactionSerializer(
            data={
                'transaction_type': transaction_type,
                'items': [{'inventory': inventory.id, 'quantity': quantity}],
            },
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
