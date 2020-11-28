from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(Member)
class MemberAdmin(UserAdmin):

    model = Member
    list_display = [
        '_nameAll',
        'team',
        'role',
        'email',
        'mobile',
    ]
    list_filter = ('role', 'team' )

    def _nameAll(self, obj):
        return '{} ({})'.format(obj.name, obj.username)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):

    model = Team
    list_display = [ 'name' ]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):

    model = Role
    list_display = [ 'name' ]
