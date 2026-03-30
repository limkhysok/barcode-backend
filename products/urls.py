# urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProductViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]