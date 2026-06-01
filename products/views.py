from __future__ import annotations

from typing import Any

from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Count, Q, QuerySet, Sum
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from .models import Product
from .serializers import ProductSerializer
from users.permissions import RBACPermission
from users.utils import log_activity


ALLOWED_ORDERINGS = {
    'id', '-id',
    'barcode', '-barcode',
    'product_name', '-product_name',
    'category', '-category',
    'supplier', '-supplier',
    'cost_per_unit', '-cost_per_unit',
    'reorder_level', '-reorder_level',
    'created_at', '-created_at',
}


class ProductViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = Product.objects.select_related('created_by')
    serializer_class = ProductSerializer
    permission_classes = [RBACPermission]

    def get_queryset(self) -> QuerySet[Product, Product]:
        queryset: QuerySet[Product, Product] = super().get_queryset()  # type: ignore[assignment]
        params = self.request.query_params

        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(barcode__icontains=search) |
                Q(product_name__icontains=search) |
                Q(supplier__icontains=search)
            )

        category = params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)

        supplier = params.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier__iexact=supplier)

        ordering = params.get('ordering')
        if ordering in ALLOWED_ORDERINGS:
            queryset = queryset.order_by(ordering)

        return queryset

    def list(self, request: Request, *_args: Any, **_kwargs: Any) -> Response:
        params = request.query_params.urlencode()
        cache_key = f"product_list_{params}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        queryset: QuerySet[Product, Product] = self.filter_queryset(self.get_queryset())  # type: ignore[assignment]
        serializer: BaseSerializer[Any] = self.get_serializer(queryset, many=True)  # type: ignore[assignment]
        response_data: dict[str, Any] = {'count': len(serializer.data), 'results': serializer.data}

        cache.set(cache_key, response_data, 120)  # 2 minutes
        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request: Request) -> Response:
        """
        GET /api/v1/products/stats/
        Returns aggregate overview — not paginated.
        """
        cache_key = "product_stats_overview"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        by_category_qs = list(
            Product.objects.values('category')
            .annotate(count=Count('id'), total_value=Sum('cost_per_unit'))
            .order_by('category')
        )

        total_products = sum(row['count'] for row in by_category_qs)
        total_value = sum(row['total_value'] or 0 for row in by_category_qs)

        response_data: dict[str, Any] = {
            "total_products": total_products,
            "total_value": total_value,
            "by_category": {
                row['category']: {
                    "count": row['count'],
                    "total_value": row['total_value'] or 0,
                }
                for row in by_category_qs
            },
        }

        cache.set(cache_key, response_data, 300)  # 5 minutes
        return Response(response_data)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer: BaseSerializer[Any] = self.get_serializer(data=request.data)  # type: ignore[assignment]
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(
                {"detail": "A product with this barcode already exists."},
                status=status.HTTP_409_CONFLICT,
            )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        obj = serializer.save(created_by=self.request.user)
        log_activity(self.request, 'product_created', {
            'product_id': obj.id,
            'product_name': obj.product_name,
            'barcode': obj.barcode,
        })

    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        obj = serializer.save()
        log_activity(self.request, 'product_updated', {
            'product_id': obj.id,
            'product_name': obj.product_name,
            'barcode': obj.barcode,
        })

    def perform_destroy(self, instance: Any) -> None:
        log_activity(self.request, 'product_deleted', {
            'product_id': instance.id,
            'product_name': instance.product_name,
            'barcode': instance.barcode,
        })
        instance.delete()

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            return super().destroy(request, *args, **kwargs)  # type: ignore[no-any-return]
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete product with existing inventory records or transactions."},
                status=status.HTTP_409_CONFLICT,
            )
