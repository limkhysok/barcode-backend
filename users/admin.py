from __future__ import annotations

from typing import Any, cast

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils import timezone
from core.admin_site import admin_site
from .models import User, UserActivity


ACTION_ICONS = {
    ADDITION: ("➕", "Added"),
    CHANGE: ("✏️", "Changed"),
    DELETION: ("🗑", "Deleted"),
}


class AdminActionLogInline(admin.TabularInline):  # type: ignore[type-arg]
    """Shows Django's built-in admin action history performed BY this user."""

    model = LogEntry
    fk_name = "user"
    extra = 0
    can_delete = False
    max_num = 0
    verbose_name = "Admin Action"
    verbose_name_plural = "Admin Actions (built-in history)"
    readonly_fields = (
        "action_time",
        "action_flag_display",
        "content_type",
        "object_repr",
        "change_message",
    )
    fields = (
        "action_time",
        "action_flag_display",
        "content_type",
        "object_repr",
        "change_message",
    )

    @admin.display(description="Action")
    def action_flag_display(self, obj: Any) -> Any:
        icon, label = ACTION_ICONS.get(obj.action_flag, ("?", "Unknown"))
        return format_html("{} {}", icon, label)

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


class UserActivityInline(admin.TabularInline):  # type: ignore[type-arg]
    """Shows login/logout/register activity logged by our app."""

    model = UserActivity
    extra = 0
    readonly_fields = ("action", "timestamp", "ip_address", "user_agent", "details")
    can_delete = False
    max_num = 0
    verbose_name = "Activity"
    verbose_name_plural = "User Activities"

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


@admin.register(User, site=admin_site)
class UserAdmin(BaseUserAdmin):  # type: ignore[type-arg]
    fieldsets: Any = BaseUserAdmin.fieldsets + (  # type: ignore[operator]
        ("Personal Info", {"fields": ("name",)}),
        ("Role", {"fields": ("is_boss",)}),
    )
    add_fieldsets: Any = BaseUserAdmin.add_fieldsets + (  # type: ignore[operator]
        (None, {"fields": ("name", "is_boss")}),
    )

    list_display = (
        "username",
        "email",
        "name",
        "is_boss",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
        "last_login",
        "activity_log_count",
        "admin_action_count",
    )

    search_fields = ("username", "email", "name", "first_name", "last_name")
    list_filter = ("is_boss", "is_staff", "is_superuser", "is_active")
    list_editable = ("is_boss", "is_active")
    ordering = ("-date_joined",)
    inlines: Any = [UserActivityInline, AdminActionLogInline]

    @admin.display(description="Activities")
    def activity_log_count(self, obj: Any) -> Any:
        count = obj.activities.count()
        return format_html(
            '<a href="/admin/users/useractivity/?user__id__exact={}">{}</a>',
            obj.pk,
            count,
        )

    @admin.display(description="Admin Actions")
    def admin_action_count(self, obj: Any) -> Any:
        count = LogEntry.objects.filter(user=obj).count()
        return format_html(
            '<a href="/admin/admin/logentry/?user__id__exact={}">{}</a>',
            obj.pk,
            count,
        )


@admin.register(UserActivity, site=admin_site)
class UserActivityAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "action", "timestamp", "ip_address", "user_agent_short", "details")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "user__email", "ip_address", "user_agent")
    readonly_fields = ("user", "action", "timestamp", "ip_address", "user_agent", "details")
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"

    @admin.display(description="User Agent")
    def user_agent_short(self, obj: UserActivity) -> str:
        ua = cast(str, obj.user_agent)  # type: ignore[reportUnknownMemberType]
        return ua[:60] + "..." if len(ua) > 60 else ua

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


@admin.register(LogEntry, site=admin_site)
class LogEntryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("action_time", "user", "content_type", "object_repr", "action_flag_display", "change_message")
    list_filter = ("action_flag", "content_type", "action_time")
    search_fields = ("user__username", "object_repr", "change_message")
    readonly_fields = ("action_time", "user", "content_type", "object_id", "object_repr", "action_flag", "change_message")
    ordering = ("-action_time",)
    date_hierarchy = "action_time"

    @admin.display(description="Action")
    def action_flag_display(self, obj: Any) -> Any:
        icon, label = ACTION_ICONS.get(obj.action_flag, ("?", "Unknown"))
        return format_html("{} {}", icon, label)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return bool(getattr(request.user, 'is_superuser', False))


@admin.register(ContentType, site=admin_site)
class ContentTypeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("app_label", "model")
    list_filter = ("app_label",)
    search_fields = ("app_label", "model")
    ordering = ("app_label", "model")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return bool(getattr(request.user, 'is_superuser', False))


@admin.register(Session, site=admin_site)
class SessionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("session_key", "expire_date", "is_expired", "decoded_preview")
    list_filter = ("expire_date",)
    search_fields = ("session_key",)
    readonly_fields = ("session_key", "expire_date", "session_data", "decoded_data")
    ordering = ("-expire_date",)
    date_hierarchy = "expire_date"

    @admin.display(description="Status")
    def is_expired(self, obj: Session) -> Any:
        expired = obj.expire_date < timezone.now()  # type: ignore[reportUnknownMemberType]
        return format_html(
            '<span style="color:{};">{}</span>',
            "red" if expired else "green",
            "Expired" if expired else "Active",
        )

    @admin.display(description="Session Preview")
    def decoded_preview(self, obj: Session) -> str:
        try:
            data = obj.get_decoded()
            preview = str(data)[:120]
            return preview + "..." if len(str(data)) > 120 else preview
        except Exception:
            return "(unreadable)"

    @admin.display(description="Full Decoded Data")
    def decoded_data(self, obj: Session) -> Any:
        try:
            return obj.get_decoded()
        except Exception:
            return "(unreadable)"

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return bool(getattr(request.user, 'is_superuser', False))


@admin.register(Permission, site=admin_site)
class PermissionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "content_type", "codename")
    list_filter = ("content_type__app_label",)
    search_fields = ("name", "codename", "content_type__app_label", "content_type__model")
    ordering = ("content_type__app_label", "content_type__model", "codename")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return bool(getattr(request.user, 'is_superuser', False))

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return bool(getattr(request.user, 'is_superuser', False))

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return bool(getattr(request.user, 'is_superuser', False))


@admin.register(Group, site=admin_site)
class GroupAdmin(BaseGroupAdmin):  # type: ignore[type-arg]
    list_display = ("name", "user_count", "permission_count")
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="Users")
    def user_count(self, obj: Group) -> int:
        return obj.user_set.count()  # type: ignore[attr-defined]

    @admin.display(description="Permissions")
    def permission_count(self, obj: Group) -> int:
        return int(obj.permissions.count())  # type: ignore[reportUnknownMemberType]
