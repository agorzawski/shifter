from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from members.models import Member, Team, Role


@admin.register(Member)
class MemberAdmin(UserAdmin):
    model = Member
    list_display = [
        '_nameAll',
        'is_staff',
        'is_superuser',
        'team',
        'role',
        'email',
        'mobile',
    ]
    list_filter = ('role', 'team')

    fieldsets = (
        (None, {'fields': (
            'username',
            'password',
        )}),
        (_('Member info'), {'fields': (
            'first_name',
            'last_name',
            'role',
            'team',
            'email',
            'mobile',
            'photo',
        )}),
        (_('Permissions'), {'fields': (
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        ), 'classes': ('collapse',)}),
        (_('Important dates'), {'fields': (
            'last_login',
            'date_joined',
        ), 'classes': ('collapse',)}),
    )

    def _nameAll(self, obj):
        return '{} ({})'.format(obj.name, obj.username)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    model = Team
    list_display = ['name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    model = Role
    list_display = ['name', 'abbreviation', 'priority']
