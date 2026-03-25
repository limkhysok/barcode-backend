from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'', InventoryViewSet, basename='inventory')

urlpatterns = [
    path('', include(router.urls)),
]
