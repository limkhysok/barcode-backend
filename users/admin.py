from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.utils.html import format_html
from .models import User, UserActivityLog


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


class UserActivityLogInline(admin.TabularInline):
    """Shows login/logout/register activity logged by our app."""

    model = UserActivityLog
    extra = 0
    readonly_fields = ("action", "timestamp", "ip_address", "details")
    can_delete = False
    max_num = 0
    verbose_name = "Activity Log"
    verbose_name_plural = "Login / API Activity Logs"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(User)
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
    inlines = [UserActivityLogInline, AdminActionLogInline]

    def activity_log_count(self, obj):
        count = obj.activity_logs.count()
        return format_html(
            '<a href="/admin/users/useractivitylog/?user__id__exact={}">{}</a>',
            obj.pk,
            count,
        )

    activity_log_count.short_description = "Login Logs"

    def admin_action_count(self, obj):
        count = LogEntry.objects.filter(user=obj).count()
        return format_html(
            '<a href="/admin/admin/logentry/?user__id__exact={}">{}</a>',
            obj.pk,
            count,
        )

    admin_action_count.short_description = "Admin Actions"


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp", "ip_address", "details_short")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "user__email", "ip_address", "details")
    readonly_fields = ("user", "action", "timestamp", "ip_address", "details")
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"

    def details_short(self, obj):
        return obj.details[:80] + "..." if len(obj.details) > 80 else obj.details

    details_short.short_description = "Details"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
