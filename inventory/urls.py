from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import InventoryViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'', InventoryViewSet, basename='inventory')

urlpatterns = [
    path('', include(router.urls)),
]
