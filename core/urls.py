from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Delegate to app-specific URL files with versioning
    path('api/v1/users/', include('users.urls')),
    path('api/v1/products/', include('products.urls')),
    path('api/v1/inventory/', include('inventory.urls')),
    path('api/v1/transactions/', include('transactions.urls')),
]
