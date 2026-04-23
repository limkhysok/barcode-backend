from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.admin_site import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/v1/auth/', include('users.auth_urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/admin/', include('users.admin_urls')),
    path('api/v1/products/', include('products.urls')),
    path('api/v1/inventory/', include('inventory.urls')),
    path('api/v1/transactions/', include('transactions.urls')),
    path('api/v1/dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
