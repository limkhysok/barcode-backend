from datetime import timedelta
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Inventory
from .serializers import InventorySerializer
from products.models import Product
from users.permissions import RBACPermission


DEFAULT_PAGE_SIZE = 20
ALLOWED_PAGE_SIZES = {20, 50, 100, 200, 500, 1000}

ALLOWED_ORDERINGS = {
    'product_name', '-product_name',
    'site', '-site',
    'location', '-location',
    'reorder_status', '-reorder_status',
    'updated_at', '-updated_at',
    'quantity_on_hand', '-quantity_on_hand',
}


class InventoryViewSet(viewsets.ModelViewSet):
    """
    Explore and manage inventory (site tracking, stock counts, and locations).

    Query params for list:
      ?product_id=<id>              - filter by product
      ?site=<name>                  - filter by site (case-insensitive)
      ?search=<term>                - search by product name (for transaction page dropdown)
      ?ordering=<field>             - sort results (e.g., quantity_on_hand, -updated_at)
      ?page_size=<n>                - limit results (20, 50, 100, 200, 500, 1000 or 'all')
                                      defaults to 20

    Extra actions:
      GET /api/v1/inventory/scan/?barcode=<barcode>
        - Look up inventory records by product barcode (for scan page).
        - Returns { found, product, inventory } regardless of whether the
          product exists in inventory, so the frontend can show the right UI.
    """
    queryset = Inventory.objects.select_related('product').order_by('-updated_at')
    serializer_class = InventorySerializer
    permission_classes = [RBACPermission]
    pagination_class = None  # Disable global page-number pagination

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        product_id = params.get('product_id')
        site_name = params.get('site')
        search = params.get('search')
        reorder_status = params.get('reorder_status')

        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if site_name:
            # Matches SITE A, SITE B, SITE C, SITE D etc. (inclusive icontains)
            queryset = queryset.filter(site__icontains=site_name)
        if reorder_status:
            # Handles 'Yes' or 'No' (standardized case-insensitive)
            queryset = queryset.filter(reorder_status__iexact=reorder_status)
        if search:
            queryset = queryset.filter(product__product_name__icontains=search)

        ordering = params.get('ordering')
        if ordering in ALLOWED_ORDERINGS:
            # Map aliases to model fields
            if ordering == 'product_name':
                ordering = 'product__product_name'
            elif ordering == '-product_name':
                ordering = '-product__product_name'
            
            queryset = queryset.order_by(ordering)

        return queryset

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        raw = request.query_params.get('page_size', '').strip().lower()
        if raw == 'all':
            limit = None
        else:
            try:
                size = int(raw)
                limit = size if size in ALLOWED_PAGE_SIZES else DEFAULT_PAGE_SIZE
            except (ValueError, TypeError):
                limit = DEFAULT_PAGE_SIZE

        total = queryset.count()
        if limit is not None:
            queryset = queryset[:limit]

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': total,
            'page_size': limit if limit is not None else total,
            'results': serializer.data,
        })

    def _activity_data(self, qs, days, group_by='day'):
        """
        Return new inventory records created within the last `days` days,
        grouped by day (for 7/14/30-day windows) or by week (for 3-month window).
        Missing dates/weeks are not included — frontend fills zeros.
        """
        cutoff = timezone.now() - timedelta(days=days)
        filtered = qs.filter(created_at__gte=cutoff)

        if group_by == 'week':
            rows = (
                filtered
                .annotate(period=TruncWeek('created_at'))
                .values('period')
                .annotate(new_records=Count('id'))
                .order_by('period')
            )
            return [
                {'week_start': row['period'].date().isoformat(), 'new_records': row['new_records']}
                for row in rows
            ]

        rows = (
            filtered
            .annotate(period=TruncDate('created_at'))
            .values('period')
            .annotate(new_records=Count('id'))
            .order_by('period')
        )
        return [
            {'date': row['period'].isoformat(), 'new_records': row['new_records']}
            for row in rows
        ]

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /api/v1/inventory/stats/
        Returns aggregate overview + time-based activity — not paginated.
        """
        qs = Inventory.objects.all()

        totals = qs.aggregate(
            total_records=Count('id'),
            total_quantity=Sum('quantity_on_hand'),
            total_stock_value=Sum('stock_value'),
            needs_reorder=Count('id', filter=Q(reorder_status='Yes')),
        )

        by_site = (
            qs.values('site')
            .annotate(
                records=Count('id'),
                total_quantity=Sum('quantity_on_hand'),
                total_stock_value=Sum('stock_value'),
            )
            .order_by('site')
        )

        return Response({
            "total_records": totals['total_records'],
            "total_quantity_on_hand": totals['total_quantity'] or 0,
            "total_stock_value": totals['total_stock_value'] or 0,
            "needs_reorder": totals['needs_reorder'],
            "by_site": {
                row['site']: {
                    "records": row['records'],
                    "total_quantity_on_hand": row['total_quantity'] or 0,
                    "total_stock_value": row['total_stock_value'] or 0,
                }
                for row in by_site
            },
            "activity": {
                "last_7_days":    {"data": self._activity_data(qs, 7,   'day')},
                "last_14_days":   {"data": self._activity_data(qs, 14,  'day')},
                "last_30_days":   {"data": self._activity_data(qs, 30,  'day')},
                "last_3_months":  {"data": self._activity_data(qs, 90,  'week')},
            },
        })

    @action(detail=False, methods=['get'], url_path='scan')
    def scan(self, request):
        """
        GET /api/v1/inventory/scan/?barcode=SN-XXXXXX

        Used by the scan page. Returns:
          {
            "found": true,
            "product": { id, barcode, product_name, ... },
            "inventory": [ { id, site, location, quantity_on_hand, ... }, ... ]
          }

        If the barcode does not match any product, returns 404 with found=false.
        If the product exists but has no inventory record, found=false with the
        product info so the frontend can show "not in inventory" rather than
        "unknown barcode".
        """
        barcode = request.query_params.get('barcode', '').strip()
        if not barcode:
            return Response(
                {"detail": "barcode query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            return Response(
                {"found": False, "detail": "No product found with this barcode."},
                status=status.HTTP_404_NOT_FOUND,
            )

        inventory_qs = Inventory.objects.filter(product=product).order_by('site', 'location')
        inventory_data = InventorySerializer(inventory_qs, many=True).data

        from products.serializers import ProductSerializer
        return Response({
            "found": inventory_qs.exists(),
            "product": ProductSerializer(product).data,
            "inventory": inventory_data,
        })
