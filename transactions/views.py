import csv
from datetime import timedelta
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction, TransactionItem
from .serializers import TransactionSerializer
from products.models import Product
from inventory.models import Inventory
from inventory.serializers import InventorySerializer
from users.permissions import RBACPermission
from users.utils import log_activity


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Log and manage stock transactions (Receive / Sale).
    Each transaction has a single type and can contain multiple items.
    """
    queryset = Transaction.objects.select_related('performed_by').prefetch_related('items__inventory__product').all()
    serializer_class = TransactionSerializer
    permission_classes = [RBACPermission]
    pagination_class = None

    def perform_create(self, serializer):
        instance = serializer.save()
        log_activity(self.request, 'transaction_created', {
            'transaction_id': instance.id,
            'type': instance.transaction_type,
            'item_count': instance.items.count(),
        })

    def perform_destroy(self, instance):
        log_activity(self.request, 'transaction_deleted', {
            'transaction_id': instance.id,
            'type': instance.transaction_type,
        })
        instance.delete()

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
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        by_type = list(
            Transaction.objects.values('transaction_type')
            .annotate(
                total_count=Count('id'),
                today_count=Count('id', filter=Q(
                    transaction_date__gte=today_start, transaction_date__lt=today_end
                )),
                today_total_quantity=Sum('items__quantity', filter=Q(
                    transaction_date__gte=today_start, transaction_date__lt=today_end
                )),
            )
            .order_by('transaction_type')
        )

        by_type_result = {
            row['transaction_type']: {
                "total_count": row['total_count'],
                "today_count": row['today_count'],
                "today_total_quantity": row['today_total_quantity'] or 0,
            }
            for row in by_type
        }

        return Response({
            "total_transactions": sum(row['total_count'] for row in by_type),
            "today_transactions": sum(row['today_count'] for row in by_type),
            "by_type": by_type_result,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """
        GET /api/v1/transactions/export/
        Export transactions for a given day as CSV.
        Query params:
          - date: YYYY-MM-DD (defaults to today)
          - type: Receive | Sale (optional, omit for both)
        """
        # Resolve date
        date_param = request.query_params.get('date')
        if date_param:
            try:
                from datetime import date as date_cls
                export_date = date_cls.fromisoformat(date_param)
            except ValueError:
                return Response(
                    {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            export_date = timezone.now().date()

        # Resolve optional type filter
        transaction_type = request.query_params.get('type')
        if transaction_type and transaction_type not in ('Receive', 'Sale'):
            return Response(
                {'detail': 'Invalid type. Use Receive or Sale.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            TransactionItem.objects
            .select_related(
                'transaction',
                'transaction__performed_by',
                'inventory__product',
                'inventory',
            )
            .filter(transaction__transaction_date__date=export_date)
        )
        if transaction_type:
            qs = qs.filter(transaction__transaction_type=transaction_type)

        qs = qs.order_by('transaction__transaction_date', 'transaction__id', 'id')

        filename = f"transactions_{export_date}"
        if transaction_type:
            filename += f"_{transaction_type.lower()}"
        filename += ".csv"

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'transaction_id',
            'transaction_type',
            'transaction_date',
            'performed_by',
            'product_name',
            'barcode',
            'site',
            'location',
            'quantity',
            'cost_per_unit',
            'line_total',
        ])

        for item in qs:
            txn = item.transaction
            inv = item.inventory
            product = inv.product
            writer.writerow([
                txn.id,
                txn.transaction_type,
                txn.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                txn.performed_by.username if txn.performed_by else '',
                product.product_name,
                product.barcode,
                inv.site,
                inv.location,
                item.quantity,
                item.cost_per_unit,
                item.line_total,
            ])

        return response

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
            txn = serializer.save()
            log_activity(self.request, 'transaction_created', {
                'transaction_id': txn.id,
                'type': txn.transaction_type,
                'item_count': 1,
                'via': 'scan',
            })
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
