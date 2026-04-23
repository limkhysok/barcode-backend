from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.utils.html import format_html
from django.utils import timezone
from core.admin_site import admin_site
from .models import User, UserActivity


ACTION_ICONS = {
    ADDITION: ("➕", "Added"),
    CHANGE: ("✏️", "Changed"),
    DELETION: ("🗑", "Deleted"),
}


class AdminActionLogInline(admin.TabularInline):
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

    def action_flag_display(self, obj):
        icon, label = ACTION_ICONS.get(obj.action_flag, ("?", "Unknown"))
        return format_html("{} {}", icon, label)

    action_flag_display.short_description = "Action"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class UserActivityInline(admin.TabularInline):
    """Shows login/logout/register activity logged by our app."""

    model = UserActivity
    extra = 0
    readonly_fields = ("action", "timestamp", "ip_address", "user_agent", "details")
    can_delete = False
    max_num = 0
    verbose_name = "Activity"
    verbose_name_plural = "User Activities"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(User, site=admin_site)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Personal Info", {"fields": ("name",)}),
        ("Role", {"fields": ("is_boss",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
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
    inlines = [UserActivityInline, AdminActionLogInline]

    def activity_log_count(self, obj):
        count = obj.activities.count()
        return format_html(
            '<a href="/admin/users/useractivity/?user__id__exact={}">{}</a>',
            obj.pk,
            count,
        )

    activity_log_count.short_description = "Activities"

    def admin_action_count(self, obj):
        count = LogEntry.objects.filter(user=obj).count()
        return format_html(
            '<a href="/admin/admin/logentry/?user__id__exact={}">{}</a>',
            obj.pk,
            count,
        )

    admin_action_count.short_description = "Admin Actions"


@admin.register(UserActivity, site=admin_site)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp", "ip_address", "user_agent_short", "details")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "user__email", "ip_address", "user_agent")
    readonly_fields = ("user", "action", "timestamp", "ip_address", "user_agent", "details")
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"

    def user_agent_short(self, obj):
        return obj.user_agent[:60] + "..." if len(obj.user_agent) > 60 else obj.user_agent

    user_agent_short.short_description = "User Agent"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# Django built-in: LogEntry (standalone view, full audit trail)
# ---------------------------------------------------------------------------
@admin.register(LogEntry, site=admin_site)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("action_time", "user", "content_type", "object_repr", "action_flag_display", "change_message")
    list_filter = ("action_flag", "content_type", "action_time")
    search_fields = ("user__username", "object_repr", "change_message")
    readonly_fields = ("action_time", "user", "content_type", "object_id", "object_repr", "action_flag", "change_message")
    ordering = ("-action_time",)
    date_hierarchy = "action_time"

    def action_flag_display(self, obj):
        icon, label = ACTION_ICONS.get(obj.action_flag, ("?", "Unknown"))
        return format_html("{} {}", icon, label)

    action_flag_display.short_description = "Action"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ---------------------------------------------------------------------------
# Django built-in: ContentType
# ---------------------------------------------------------------------------
@admin.register(ContentType, site=admin_site)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ("app_label", "model")
    list_filter = ("app_label",)
    search_fields = ("app_label", "model")
    ordering = ("app_label", "model")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ---------------------------------------------------------------------------
# Django built-in: Session (with decoded data preview)
# ---------------------------------------------------------------------------
@admin.register(Session, site=admin_site)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_key", "expire_date", "is_expired", "decoded_preview")
    list_filter = ("expire_date",)
    search_fields = ("session_key",)
    readonly_fields = ("session_key", "expire_date", "session_data", "decoded_data")
    ordering = ("-expire_date",)
    date_hierarchy = "expire_date"

    def is_expired(self, obj):
        expired = obj.expire_date < timezone.now()
        return format_html(
            '<span style="color:{};">{}</span>',
            "red" if expired else "green",
            "Expired" if expired else "Active",
        )

    is_expired.short_description = "Status"

    def decoded_preview(self, obj):
        try:
            data = obj.get_decoded()
            preview = str(data)[:120]
            return preview + "..." if len(str(data)) > 120 else preview
        except Exception:
            return "(unreadable)"

    decoded_preview.short_description = "Session Preview"

    def decoded_data(self, obj):
        try:
            return obj.get_decoded()
        except Exception:
            return "(unreadable)"

    decoded_data.short_description = "Full Decoded Data"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ---------------------------------------------------------------------------
# Django built-in: Permission (enhanced read-only view)
# ---------------------------------------------------------------------------
@admin.register(Permission, site=admin_site)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "content_type", "codename")
    list_filter = ("content_type__app_label",)
    search_fields = ("name", "codename", "content_type__app_label", "content_type__model")
    ordering = ("content_type__app_label", "content_type__model", "codename")

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ---------------------------------------------------------------------------
# Unregister default Group and re-register with richer display
# ---------------------------------------------------------------------------
# admin_site starts fresh — no need to unregister


@admin.register(Group, site=admin_site)
class GroupAdmin(BaseGroupAdmin):
    list_display = ("name", "user_count", "permission_count")
    search_fields = ("name",)
    ordering = ("name",)

    def user_count(self, obj):
        return obj.user_set.count()

    user_count.short_description = "Users"

    def permission_count(self, obj):
        return obj.permissions.count()

    permission_count.short_description = "Permissions"
