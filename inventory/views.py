from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Count, Q, QuerySet, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from .models import Inventory, STATUS_LOW, STATUS_NO_STOCK
from .serializers import InventorySerializer
from products.models import Product
from products.serializers import ProductSerializer
from users.permissions import RBACPermission
from users.utils import log_activity


class InventoryViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    """
    Explore and manage inventory (site tracking, stock counts, and locations).

    Query params for list:
      ?product_id=<id>              - filter by product
      ?site=<name>                  - filter by site (case-insensitive)
      ?search=<term>                - search by product name (for transaction page dropdown)
      ?ordering=<field>             - sort results (e.g., quantity_on_hand, -updated_at)

    Extra actions:
      GET /api/v1/inventory/scan/?barcode=<barcode>
        - Look up inventory records by product barcode (for scan page).
        - Returns { found, product, inventory } regardless of whether the
          product exists in inventory, so the frontend can show the right UI.
    """
    queryset = Inventory.objects.select_related('product').order_by('-updated_at')
    serializer_class = InventorySerializer
    permission_classes = [RBACPermission]

    _ALLOWED_ORDERINGS = {
        'id', '-id',
        'quantity_on_hand', '-quantity_on_hand',
        'stock_value', '-stock_value',
        'updated_at', '-updated_at',
        'created_at', '-created_at',
        'site', '-site',
        'location', '-location',
        'reorder_status', '-reorder_status',
    }

    def get_queryset(self) -> QuerySet[Inventory, Inventory]:
        queryset: QuerySet[Inventory, Inventory] = super().get_queryset()  # type: ignore[assignment]
        params = self.request.query_params

        product_id = params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        site = params.get('site')
        if site:
            queryset = queryset.filter(site__iexact=site)

        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(product__product_name__icontains=search) |
                Q(product__barcode__icontains=search)
            )

        reorder_status = params.get('reorder_status')
        if reorder_status:
            queryset = queryset.filter(reorder_status=reorder_status)

        ordering = params.get('ordering')
        if ordering and ordering in self._ALLOWED_ORDERINGS:
            queryset = queryset.order_by(ordering)

        return queryset

    def list(self, request: Request, *_args: Any, **_kwargs: Any) -> Response:
        queryset: QuerySet[Inventory, Inventory] = self.filter_queryset(self.get_queryset())  # type: ignore[assignment]
        page = self.paginate_queryset(queryset)  # type: ignore[no-untyped-call]
        if page is not None:
            serializer: BaseSerializer[Any] = self.get_serializer(page, many=True)  # type: ignore[assignment]
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)  # type: ignore[assignment]
        return Response({'count': queryset.count(), 'next': None, 'previous': None, 'results': serializer.data})

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer: BaseSerializer[Any] = self.get_serializer(data=request.data)  # type: ignore[assignment]
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(
                {"detail": "An inventory record for this product, site, and location already exists."},
                status=status.HTTP_409_CONFLICT,
            )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def _save_and_refresh(self, serializer: BaseSerializer[Any]) -> Inventory:
        instance: Inventory = serializer.save()  # type: ignore[assignment]
        instance.refresh_stats()
        return instance

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        obj = self._save_and_refresh(serializer)
        log_activity(self.request, 'inventory_created', {
            'inventory_id': obj.id,
            'product': obj.product.product_name,
            'site': obj.site,
            'quantity': obj.quantity_on_hand,
        })

    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        obj = self._save_and_refresh(serializer)
        log_activity(self.request, 'inventory_updated', {
            'inventory_id': obj.id,
            'product': obj.product.product_name,
            'site': obj.site,
            'quantity': obj.quantity_on_hand,
        })

    def perform_destroy(self, instance: Any) -> None:
        log_activity(self.request, 'inventory_deleted', {
            'inventory_id': instance.id,
            'product': instance.product.product_name,
            'site': instance.site,
        })
        instance.delete()

    def _build_activity(self, qs: QuerySet[Inventory, Inventory]) -> dict[str, Any]:
        """
        Single DB query for 90 days of daily data, then slice in Python
        for each window (7/14/30 days daily, 90 days weekly).
        """
        cutoff = timezone.now() - timedelta(days=90)
        rows: Any = (
            qs.filter(updated_at__gte=cutoff)
            .annotate(period=TruncDate('updated_at'))
            .values('period')
            .annotate(new_records=Count('id'))
            .order_by('period')
        )
        daily: list[tuple[date, int]] = [  # type: ignore[assignment]
            (row['period'], row['new_records']) for row in rows
        ]

        today = timezone.now().date()

        def slice_days(days: int) -> list[dict[str, Any]]:
            cutoff_date = today - timedelta(days=days)
            return [
                {'date': d.isoformat(), 'new_records': n}
                for d, n in daily if d >= cutoff_date
            ]

        def to_weeks() -> list[dict[str, Any]]:
            week_totals: defaultdict[date, int] = defaultdict(int)
            for d, n in daily:
                week_start = d - timedelta(days=d.weekday())
                week_totals[week_start] += n
            return [
                {'week_start': w.isoformat(), 'new_records': n}
                for w, n in sorted(week_totals.items())
            ]

        return {
            "last_7_days":   {"data": slice_days(7)},
            "last_14_days":  {"data": slice_days(14)},
            "last_30_days":  {"data": slice_days(30)},
            "last_3_months": {"data": to_weeks()},
        }

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, _request: Request) -> Response:
        """
        GET /api/v1/inventory/stats/
        Returns aggregate overview + time-based activity — not paginated.
        """
        cache_key = "inventory_stats_overview"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        qs = Inventory.objects.all()

        totals = qs.aggregate(
            total_records=Count('id'),
            total_quantity=Sum('quantity_on_hand'),
            total_stock_value=Sum('stock_value'),
            needs_reorder=Count('id', filter=Q(reorder_status__in=[STATUS_LOW, STATUS_NO_STOCK])),
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

        response_data: dict[str, Any] = {
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
            "activity": self._build_activity(qs),
        }
        cache.set(cache_key, response_data, 300)  # 5 minutes
        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='scan')
    def scan(self, request: Request) -> Response:
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
        inventory_data: list[Any] = InventorySerializer(inventory_qs, many=True).data  # type: ignore[assignment]

        return Response({
            "found": len(inventory_data) > 0,
            "product": ProductSerializer(product).data,  # pyright: ignore[reportUnknownMemberType]
            "inventory": inventory_data,
        })
