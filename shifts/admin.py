from django.contrib import admin
from django.utils.translation import ngettext
from django.contrib import messages
# Register your models here.

from .models import *


@admin.register(ShifterMessage)
class ShifterMessageAdmin(admin.ModelAdmin):
    model = Revision
    list_display = [
        'number',
        'valid',
        'description',
    ]


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    model = Revision
    list_display = [
        'number',
        'date_start',
        'valid',
    ]


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    model = Campaign
    list_display = [
        'name',
        'revision',
        'description',
    ]
    list_filter = ('revision',)


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    model = Slot
    list_display = [
        'name',
        'op',
        'hour_start',
        'hour_end',
    ]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):

    def move_to_newest_revision(self, request, queryset):
        last_season = Revision.objects.filter(valid=True).order_by('-number').first()
        updated = queryset.update(revision=last_season)
        self.message_user(request, ngettext(
            '%d moved to the latest revision.',
            '%d moved to the latest revision',
            updated,
        ) % updated, messages.SUCCESS)
        self.description = 'Move selected shifts to the latest revision'

    model = Shift
    list_display = [
        'date',
        'slot',
        '_member',
        'role',
        'revision',
    ]

    list_filter = ('campaign', 'revision', 'csv_upload_tag', 'slot', 'member__team', 'member__role', 'role')
    ordering = ('-date',)
    actions = (move_to_newest_revision,)

    def _member(self, object):
        return '{} ({})'.format(object.member.username, object.member.team)

    def _display(self, object):
        return '{} {}'.format(object.date, object.slot)


@admin.register(ShiftRole)
class ShiftRoleAdmin(admin.ModelAdmin):
    model = ShiftRole
    list_display = [
        'name',
        'abbreviation',
        ]