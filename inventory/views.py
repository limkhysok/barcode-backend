from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Inventory
from .serializers import InventorySerializer
from products.models import Product

class InventoryViewSet(viewsets.ModelViewSet):
    """
    Explore and manage inventory (site tracking, stock counts, and locations).

    Query params for list:
      ?product_id=<id>   - filter by product
      ?site=<name>       - filter by site (case-insensitive)
      ?search=<term>     - search by product name (for transaction page dropdown)

    Extra actions:
      GET /api/inventory/scan/?barcode=<barcode>
        - Look up inventory records by product barcode (for scan page).
        - Returns { found, product, inventory } regardless of whether the
          product exists in inventory, so the frontend can show the right UI.
    """
    queryset = Inventory.objects.all().order_by('-updated_at')
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product_id')
        site_name = self.request.query_params.get('site')
        search = self.request.query_params.get('search')

        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if site_name:
            queryset = queryset.filter(site__icontains=site_name)
        if search:
            queryset = queryset.filter(product__product_name__icontains=search)

        return queryset

    @action(detail=False, methods=['get'], url_path='scan')
    def scan(self, request):
        """
        GET /api/inventory/scan/?barcode=SN-XXXXXX

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
