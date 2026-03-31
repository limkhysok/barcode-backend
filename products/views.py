from django.db import IntegrityError
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.db.models import Count, Sum
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer


ALLOWED_PAGE_SIZES = {20, 50, 100, 200, 500, 1000}

ALLOWED_ORDERINGS = {
    'id', '-id',
    'product_name', '-product_name',
    'supplier', '-supplier',
    'cost_per_unit', '-cost_per_unit',
    'reorder_level', '-reorder_level',
    'created_at', '-created_at',
}


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        raw = request.query_params.get(self.page_size_query_param, '')
        if raw.lower() == 'all':
            return None
        try:
            size = int(raw)
            if size in ALLOWED_PAGE_SIZES:
                return size
        except (ValueError, TypeError):
            pass
        return self.page_size


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('created_by')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ProductPagination

    def get_queryset(self):
        queryset = super().get_queryset()
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

        ordering = params.get('ordering')
        if ordering in ALLOWED_ORDERINGS:
            queryset = queryset.order_by(ordering)

        return queryset

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        if request.query_params.get('page_size', '').lower() == 'all':
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': len(serializer.data),
                'next': None,
                'previous': None,
                'results': serializer.data,
            })

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /api/v1/products/stats/
        Returns aggregate overview — not paginated.
        """
        by_category_qs = list(
            Product.objects.values('category')
            .annotate(count=Count('id'), total_value=Sum('cost_per_unit'))
            .order_by('category')
        )

        total_products = sum(row['count'] for row in by_category_qs)
        total_value = sum(row['total_value'] or 0 for row in by_category_qs)

        return Response({
            "total_products": total_products,
            "total_value": total_value,
            "by_category": {
                row['category']: {
                    "count": row['count'],
                    "total_value": row['total_value'] or 0,
                }
                for row in by_category_qs
            },
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete product with existing transactions."},
                status=status.HTTP_409_CONFLICT,
            )
