import csv
from datetime import timedelta
from typing import Any

from django.db.models import Count, Q, QuerySet, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from django.core.cache import cache
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from .models import Transaction, TransactionItem
from .serializers import TransactionSerializer
from products.models import Product
from inventory.models import Inventory
from inventory.serializers import InventorySerializer
from users.permissions import RBACPermission
from users.utils import log_activity


class TransactionViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    """
    Log and manage stock transactions (Receive / Sale).
    Each transaction has a single type and can contain multiple items.
    """
    queryset = Transaction.objects.select_related('performed_by').prefetch_related('items__inventory__product').all()
    serializer_class = TransactionSerializer
    permission_classes = [RBACPermission]

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        item_count: int = len(serializer.validated_data.get('items', []))
        instance: Transaction = serializer.save()  # type: ignore[assignment]
        log_activity(self.request, 'transaction_created', {
            'transaction_id': instance.id,
            'type': instance.transaction_type,
            'item_count': item_count,
        })

    def perform_destroy(self, instance: Any) -> None:
        log_activity(self.request, 'transaction_deleted', {
            'transaction_id': instance.id,
            'type': instance.transaction_type,
        })
        instance.delete()

    def get_queryset(self) -> QuerySet[Transaction, Transaction]:
        queryset: QuerySet[Transaction, Transaction] = super().get_queryset()  # type: ignore[assignment]
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
    def stats(self, request: Request) -> Response:
        """
        GET /api/v1/transactions/stats
        Returns aggregate overview — not paginated.
        """
        cache_key = "transaction_stats_overview"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        by_type: list[dict[str, Any]] = list(  # type: ignore[assignment]
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

        by_type_result: dict[str, dict[str, Any]] = {
            row['transaction_type']: {
                "total_count": row['total_count'],
                "today_count": row['today_count'],
                "today_total_quantity": row['today_total_quantity'] or 0,
            }
            for row in by_type
        }

        response_data: dict[str, Any] = {
            "total_transactions": sum(row['total_count'] for row in by_type),
            "today_transactions": sum(row['today_count'] for row in by_type),
            "by_type": by_type_result,
        }

        # Cache for 5 minutes
        cache.set(cache_key, response_data, 300)
        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request: Request) -> HttpResponse | Response:
        """
        GET /api/v1/transactions/export/
        Export transactions for a given day as CSV.
        Query params:
          - date: YYYY-MM-DD (defaults to today)
          - type: Receive | Sale (optional, omit for both)
        """
        # Resolve date
        date_param: str | None = request.query_params.get('date')
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
        transaction_type: str | None = request.query_params.get('type')
        if transaction_type and transaction_type not in ('Receive', 'Sale'):
            return Response(
                {'detail': 'Invalid type. Use Receive or Sale.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from datetime import datetime as dt
        day_start = dt(export_date.year, export_date.month, export_date.day, 0, 0, 0)
        day_end = dt(export_date.year, export_date.month, export_date.day, 23, 59, 59, 999999)
        qs = (
            TransactionItem.objects
            .select_related(
                'transaction',
                'transaction__performed_by',
                'inventory__product',
                'inventory',
            )
            .filter(transaction__transaction_date__range=(day_start, day_end))
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

        log_activity(request, 'transaction_exported', {
            'date': export_date.isoformat(),
            'type': transaction_type or 'all',
            'filename': filename,
        })

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
                txn.performed_by.get_username() if txn.performed_by else '',
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
    def scan(self, request: Request) -> Response:
        """
        Create a single-item transaction by scanning a product barcode.
        POST /api/transactions/scan
        Body: { barcode, transaction_type, quantity, inventory_id (optional) }
        """
        barcode: str | None = request.data.get('barcode')  # type: ignore[assignment]
        transaction_type: str | None = request.data.get('transaction_type')  # type: ignore[assignment]
        quantity: int | None = request.data.get('quantity')  # type: ignore[assignment]
        inventory_id: int | None = request.data.get('inventory_id')  # type: ignore[assignment]

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

        # Step 2: Find inventory records for this product (single query)
        inventory_list = list(Inventory.objects.filter(product=product))
        if not inventory_list:
            return Response(
                {'detail': 'Product found but has no inventory record.', 'product': product.product_name},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Resolve which inventory record to use
        if inventory_id:
            matched = [inv for inv in inventory_list if inv.id == inventory_id]
            if not matched:
                return Response(
                    {'detail': 'The specified inventory_id does not belong to this product.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            inventory = matched[0]
        elif len(inventory_list) == 1:
            inventory = inventory_list[0]
        else:
            return Response(
                {
                    'detail': 'Multiple inventory records found. Please specify inventory_id.',
                    'inventory': InventorySerializer(inventory_list, many=True).data,  # pyright: ignore[reportUnknownMemberType]
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
            txn: Transaction = serializer.save()  # type: ignore[assignment]
            log_activity(self.request, 'transaction_created', {
                'transaction_id': txn.id,
                'type': txn.transaction_type,
                'item_count': 1,
                'via': 'scan',
            })
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # pyright: ignore[reportUnknownMemberType]
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # pyright: ignore[reportUnknownMemberType]
