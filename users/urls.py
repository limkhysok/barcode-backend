from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, UserDetailView, api_root,
    AdminUserListView, AdminUserDetailView,
    AdminUserLogsView, AdminAllLogsView,
    BossStaffListView,
    CustomTokenObtainPairView,
)


urlpatterns = [
    path('', api_root, name='users_api_root'),
    path('register', RegisterView.as_view(), name='auth_register'),
    path('login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('me', UserDetailView.as_view(), name='user_detail'),

    # Admin user management
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:pk>/logs/', AdminUserLogsView.as_view(), name='admin_user_logs'),
    path('admin/logs/', AdminAllLogsView.as_view(), name='admin_all_logs'),

    # Boss dashboard
    path('boss/staff-users/', BossStaffListView.as_view(), name='boss_staff_list'),
]
