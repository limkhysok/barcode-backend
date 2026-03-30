from django.db.models.deletion import ProtectedError
from django.db.models import Count, Sum
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /api/v1/products/stats/
        Returns aggregate overview — not paginated.
        """
        # Per category: count + sum of cost_per_unit — query Product directly
        by_category_qs = list(
            Product.objects.values('category')
            .annotate(count=Count('id'), total_value=Sum('cost_per_unit'))
            .order_by('category')
        )

        return Response({
            "total_products": Product.objects.count(),
            "total_value": Product.objects.aggregate(t=Sum('cost_per_unit'))['t'] or 0,
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
            if 'barcode' in serializer.errors:
                return Response(
                    {"detail": "A product with this barcode already exists."},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
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
        
