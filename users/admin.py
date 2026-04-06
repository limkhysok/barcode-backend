from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Add custom fields to detailed view
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Personal Info', {'fields': ('name',)}),
        ('Role', {'fields': ('is_boss',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('name', 'is_boss')}),
    )

    list_display = (
        'username',
        'email',
        'name',
        'is_boss',
        'is_staff',
        'is_superuser',
        'is_active',
        'date_joined',
        'last_login',
    )

    search_fields = ('username', 'email', 'name', 'first_name', 'last_name')

    list_filter = ('is_boss', 'is_staff', 'is_superuser', 'is_active')

    list_editable = ('is_boss',)
    
    # Default ordering
    ordering = ('-date_joined',)
