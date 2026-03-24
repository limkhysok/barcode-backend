from rest_framework import viewsets, permissions
from .models import Inventory
from .serializers import InventorySerializer

class InventoryViewSet(viewsets.ModelViewSet):
    """
    Explore and manage inventory (site tracking, stock counts, and locations).
    """
    queryset = Inventory.objects.all().order_by('-updated_at')
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    # Optionally filter by product or site
    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product_id')
        site_name = self.request.query_params.get('site')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if site_name:
            queryset = queryset.filter(site__icontains=site_name)
            
        return queryset
