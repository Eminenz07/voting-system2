from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('matric', 'first_name', 'last_name', 'role', 'is_verified', 'date_joined')
    list_filter = ('role', 'is_verified', 'faculty')
    search_fields = ('matric', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('matric', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'email', 'faculty', 'department')}),
        ('Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('matric', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
