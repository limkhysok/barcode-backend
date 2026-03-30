from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Delegate to app-specific URL files
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/transactions/', include('transactions.urls')),
]
