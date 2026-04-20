from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .serializers import UserSerializer, UserAdminSerializer, UserActivityLogSerializer
from .models import UserActivityLog

User = get_user_model()


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@api_view(['GET'])
@permission_classes([])
def api_root(request, format=None):
    return Response({
        'register': reverse('auth_register', request=request, format=format),
        'login': reverse('token_obtain_pair', request=request, format=format),
        'token_refresh': reverse('token_refresh', request=request, format=format),
        'me': reverse('user_detail', request=request, format=format),
        'admin_users': reverse('admin_user_list', request=request, format=format),
    })


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        UserActivityLog.objects.create(
            user=user,
            action='register',
            ip_address=get_client_ip(self.request),
        )


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()
        UserActivityLog.objects.create(
            user=self.request.user,
            action='profile_update',
            ip_address=get_client_ip(self.request),
        )


class IsAdminOrBoss(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser or request.user.is_boss
        )


class IsSuperuserOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )


class AdminUserListView(generics.ListCreateAPIView):
    """Admin: list all users or create a new user."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = (IsSuperuserOrStaff,)

    def perform_create(self, serializer):
        user = serializer.save()
        UserActivityLog.objects.create(
            user=user,
            action='register',
            ip_address=get_client_ip(self.request),
            details=f'Created by admin {self.request.user.username}',
        )


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin: view, edit, or delete a specific user."""
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = (IsSuperuserOrStaff,)

    def perform_update(self, serializer):
        serializer.save()
        UserActivityLog.objects.create(
            user=serializer.instance,
            action='profile_update',
            ip_address=get_client_ip(self.request),
            details=f'Updated by admin {self.request.user.username}',
        )

    def perform_destroy(self, instance):
        UserActivityLog.objects.create(
            user=instance,
            action='other',
            ip_address=get_client_ip(self.request),
            details=f'Account deleted by admin {self.request.user.username}',
        )
        instance.delete()


class AdminUserLogsView(generics.ListAPIView):
    """Admin: list activity logs for a specific user."""
    serializer_class = UserActivityLogSerializer
    permission_classes = (IsSuperuserOrStaff,)

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        return UserActivityLog.objects.filter(user=user).order_by('-timestamp')


class AdminAllLogsView(generics.ListAPIView):
    """Admin: list all user activity logs across the system."""
    serializer_class = UserActivityLogSerializer
    permission_classes = (IsSuperuserOrStaff,)
    queryset = UserActivityLog.objects.select_related('user').order_by('-timestamp')
