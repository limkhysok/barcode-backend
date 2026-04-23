from django.urls import path
from .views import UserDetailView, api_root

urlpatterns = [
    path('', api_root, name='users_api_root'),
    path('me/', UserDetailView.as_view(), name='user_detail'),
]
