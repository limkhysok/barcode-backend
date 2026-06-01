from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ipware import get_client_ip
from .serializers import UserSerializer, UserAdminSerializer, UserActivitySerializer, CustomTokenObtainPairSerializer
from .models import UserActivity
from .permissions import IsAdminOrBoss
from .utils import log_activity

User = get_user_model()


def _get_ip(request):
    ip, _ = get_client_ip(request)
    return ip


def _get_ua(request):
    return request.META.get('HTTP_USER_AGENT', '')


@api_view(['GET'])
@permission_classes([])
def api_root(request, format=None):
    return Response({
        'auth': {
            'register': reverse('auth_register', request=request, format=format),
            'login': reverse('token_obtain_pair', request=request, format=format),
            'logout': reverse('auth_logout', request=request, format=format),
            'token_refresh': reverse('token_refresh', request=request, format=format),
        },
        'me': reverse('user_detail', request=request, format=format),
        'admin': {
            'users': reverse('admin_user_list', request=request, format=format),
            'logs': reverse('admin_all_logs', request=request, format=format),
            'staff': reverse('boss_staff_list', request=request, format=format),
        },
    })


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        username = request.data.get('username', '')
        if response.status_code == 200:
            user = User.objects.filter(username=username).first()
            UserActivity.objects.create(
                user=user,
                action='login',
                ip_address=_get_ip(request),
                user_agent=_get_ua(request),
            )
        else:
            UserActivity.objects.create(
                user=None,
                action='login_failed',
                ip_address=_get_ip(request),
                user_agent=_get_ua(request),
                details={'attempted_username': username},
            )
        return response


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        log_activity(request, 'logout')
        return Response({'detail': 'Successfully logged out.'})


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        UserActivity.objects.create(
            user=user,
            action='register',
            ip_address=_get_ip(self.request),
            user_agent=_get_ua(self.request),
        )


class PasswordChangeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'detail': 'old_password and new_password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(old_password):
            return Response(
                {'detail': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()
        log_activity(request, 'password_change')
        return Response({'detail': 'Password changed successfully.'})


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()
        log_activity(self.request, 'profile_update')


class AdminUserListView(generics.ListCreateAPIView):
    """Admin: list all users or create a new user."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminOrBoss,)

    def perform_create(self, serializer):
        user = serializer.save()
        log_activity(self.request, 'user_created', {
            'user_id': user.id,
            'username': user.username,
        })


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin: view, edit, or delete a specific user."""
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminOrBoss,)

    def perform_update(self, serializer):
        serializer.save()
        log_activity(self.request, 'user_updated', {
            'user_id': serializer.instance.id,
            'username': serializer.instance.username,
        })

    def perform_destroy(self, instance):
        log_activity(self.request, 'user_deleted', {
            'user_id': instance.id,
            'username': instance.username,
        })
        instance.delete()


class AdminUserLogsView(generics.ListAPIView):
    """Admin: list activity logs for a specific user."""
    serializer_class = UserActivitySerializer
    permission_classes = (IsAdminOrBoss,)

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        return UserActivity.objects.filter(user=user).order_by('-timestamp')


class AdminAllLogsView(generics.ListAPIView):
    """Admin: list all user activity logs across the system."""
    serializer_class = UserActivitySerializer
    permission_classes = (IsAdminOrBoss,)
    queryset = UserActivity.objects.select_related('user').order_by('-timestamp')


class BossStaffListView(generics.ListCreateAPIView):
    """Boss: list all staff users or create a new one."""
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminOrBoss,)

    def get_queryset(self):
        return User.objects.filter(is_staff=True, is_superuser=False).order_by('username')

    def perform_create(self, serializer):
        user = serializer.save()
        log_activity(self.request, 'user_created', {
            'user_id': user.id,
            'username': user.username,
            'via': 'boss_dashboard',
        })


class BossStaffDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Boss: view, edit, or delete a specific staff user."""
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminOrBoss,)

    def perform_update(self, serializer):
        user = serializer.save()
        log_activity(self.request, 'user_updated', {
            'user_id': user.id,
            'username': user.username,
            'via': 'boss_dashboard',
        })

    def perform_destroy(self, instance):
        log_activity(self.request, 'user_deleted', {
            'user_id': instance.id,
            'username': instance.username,
            'via': 'boss_dashboard',
        })
        instance.delete()
