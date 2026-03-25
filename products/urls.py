# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

# Remove trailing_slash=False to stick to Django's cleaner default behavior
router = DefaultRouter() 
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]