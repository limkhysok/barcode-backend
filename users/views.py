from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ipware import get_client_ip
from .serializers import UserSerializer, UserAdminSerializer, UserActivitySerializer, CustomTokenObtainPairSerializer
from .models import UserActivity
from .permissions import IsAdminOrBoss

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
        'register': reverse('auth_register', request=request, format=format),
        'login': reverse('token_obtain_pair', request=request, format=format),
        'token_refresh': reverse('token_refresh', request=request, format=format),
        'me': reverse('user_detail', request=request, format=format),
        'admin_users': reverse('admin_user_list', request=request, format=format),
    })


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get('username', '')
            user = User.objects.filter(username=username).first()
            UserActivity.objects.create(
                user=user,
                action='login',
                ip_address=_get_ip(request),
                user_agent=_get_ua(request),
            )
        return response


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


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()
        UserActivity.objects.create(
            user=self.request.user,
            action='profile_update',
            ip_address=_get_ip(self.request),
            user_agent=_get_ua(self.request),
        )




class AdminUserListView(generics.ListCreateAPIView):
    """Admin: list all users or create a new user."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminOrBoss,)

    def perform_create(self, serializer):
        user = serializer.save()
        UserActivity.objects.create(
            user=user,
            action='register',
            ip_address=_get_ip(self.request),
            user_agent=_get_ua(self.request),
            details={'created_by': self.request.user.username},
        )


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin: view, edit, or delete a specific user."""
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminOrBoss,)

    def perform_update(self, serializer):
        serializer.save()
        UserActivity.objects.create(
            user=serializer.instance,
            action='profile_update',
            ip_address=_get_ip(self.request),
            user_agent=_get_ua(self.request),
            details={'updated_by': self.request.user.username},
        )

    def perform_destroy(self, instance):
        UserActivity.objects.create(
            user=instance,
            action='other',
            ip_address=_get_ip(self.request),
            user_agent=_get_ua(self.request),
            details={'deleted_by': self.request.user.username},
        )
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


class BossStaffListView(generics.ListAPIView):
    """Boss: list all staff users (is_staff=True, excluding superusers)."""
    serializer_class = UserSerializer
    permission_classes = (IsAdminOrBoss,)

    def get_queryset(self):
        return User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
