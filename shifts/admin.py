from django.contrib import admin

# Register your models here.

from .models import *

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):

    model = Campaign
    list_display = [
        'name',
        'description',
    ]

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
        'slot',
        '_member',
    ]

    list_filter = ('campaign', 'slot', 'member__team', 'member__role')
    ordering = ('-date', )

    def _member(self, object):
        return '{} ({})'.format(object.member.username, object.member.team)

    def _display(self, object):
        return '{} {}'.format(object.date, object.slot)
