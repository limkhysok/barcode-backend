from django.urls import path
from .views import (
    AdminUserListView, AdminUserDetailView,
    AdminUserLogsView, AdminAllLogsView,
    BossStaffListView, BossStaffDetailView,
)

urlpatterns = [
    path('users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('users/<int:pk>/logs/', AdminUserLogsView.as_view(), name='admin_user_logs'),
    path('logs/', AdminAllLogsView.as_view(), name='admin_all_logs'),
    path('staff/', BossStaffListView.as_view(), name='boss_staff_list'),
    path('staff/<int:pk>/', BossStaffDetailView.as_view(), name='boss_staff_detail'),
]
