from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer  # type: ignore[import-untyped]
from .models import UserActivity

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):  # type: ignore[misc]
    @classmethod
    def get_token(cls, user: AbstractBaseUser) -> Any:
        token = super().get_token(user)
        token['username'] = user.username  # type: ignore[attr-defined]
        token['is_boss'] = user.is_boss  # type: ignore[attr-defined]
        token['is_staff'] = user.is_staff  # type: ignore[attr-defined]
        token['is_superuser'] = user.is_superuser  # type: ignore[attr-defined]
        return token


class UserSerializer(serializers.ModelSerializer[Any]):
    class Meta:  # type: ignore[override]
        model = User
        fields = (
            'id', 'username', 'email', 'name', 'password',
            'is_boss', 'is_staff', 'is_superuser'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'read_only': False},
            'is_boss': {'read_only': True},
            'is_staff': {'read_only': True},
            'is_superuser': {'read_only': True},
        }

    def create(self, validated_data: dict[str, Any]) -> Any:
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password is not None:
            instance.set_password(password)
            instance.save()
        return instance


class UserAdminSerializer(serializers.ModelSerializer[Any]):
    """Full serializer for admin — role fields are writable."""
    class Meta:  # type: ignore[override]
        model = User
        fields = (
            'id', 'username', 'email', 'name', 'password',
            'is_boss', 'is_staff', 'is_superuser', 'is_active',
            'date_joined', 'last_login',
        )
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'date_joined': {'read_only': True},
            'last_login': {'read_only': True},
        }

    def create(self, validated_data: dict[str, Any]) -> Any:
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get('request')
        if request:
            if not request.user.is_superuser:
                attrs.pop('is_superuser', None)
            if not (request.user.is_superuser or getattr(request.user, 'is_boss', False)):
                attrs.pop('is_staff', None)
        return attrs

    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password is not None:
            instance.set_password(password)
            instance.save()
        return instance


class UserActivitySerializer(serializers.ModelSerializer[Any]):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:  # type: ignore[override]
        model = UserActivity
        fields = ('id', 'user', 'username', 'action', 'timestamp', 'ip_address', 'user_agent', 'details')
