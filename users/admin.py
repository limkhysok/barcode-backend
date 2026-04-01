from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Add custom fields to detailed view
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Personal Info', {'fields': ('name',)}),
    )
    # Add additional customization to form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('name',)}),
    )

    # Show more fields in the user list view
    list_display = (
        'username', 
        'email', 
        'name',
        'is_staff', 
        'is_active',
        'date_joined',
        'last_login',
    )
    
    # Search functions
    search_fields = ('username', 'email', 'name', 'first_name', 'last_name')
    
    # Filter functions
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    
    # Default ordering
    ordering = ('-date_joined',)
