from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from members.models import Member, Team, Role
from guardian.admin import GuardedModelAdmin


@admin.register(Member)
class MemberAdmin(UserAdmin):
    model = Member
    list_display = [
        '_nameAll',
        'is_staff',
        'is_superuser',
        'is_active',
        'team',
        'role',
        'mobile',
        'email',
        'notification_shifts',
        'notification_studies'
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
            'is_active',
            'notification_shifts',
            'notification_studies'
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
class TeamAdmin(GuardedModelAdmin):
    model = Team
    list_display = ['name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    model = Role
    list_display = ['name', 'abbreviation', 'priority']
