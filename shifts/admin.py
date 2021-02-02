from django.contrib import admin

# Register your models here.

from .models import *


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
        'description',
    ]
    list_filter = ('revision',)


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    model = Slot
    list_display = [
        'name',
        'hour_start',
        'hour_end',
    ]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    model = Shift
    list_display = [
        'date',
        'revision',
        'slot',
        '_member',
    ]

    list_filter = ('campaign', 'revision', 'slot', 'member__team', 'member__role')
    ordering = ('-date',)

    def _member(self, object):
        return '{} ({})'.format(object.member.username, object.member.team)

    def _display(self, object):
        return '{} {}'.format(object.date, object.slot)
