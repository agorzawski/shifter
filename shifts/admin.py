from django.contrib import admin
from django.utils.translation import ngettext
from django.contrib import messages
# Register your models here.

from shifts.models import ShifterMessage, Revision, Campaign, Slot, Shift, ShiftRole, ShiftID, Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    model = Contact
    list_display = [
        'active',
        'fa_icon',
        'contact_type',
        'contact',
        'name'
    ]


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
        'name',
        'number',
        'date_start',
        'valid',
        'ready_for_preview',
        'merged',
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

    def move_to_op_TRUE(self, request, queryset):
        updated = queryset.update(op=True)
        self.message_user(request, ngettext(
            '%d slots was set to TRUE.',
            '%d slots were set to TRUE status',
            updated,
        ) % updated, messages.SUCCESS)

    def move_to_op_FALSE(self, request, queryset):
        updated = queryset.update(op=False)
        self.message_user(request, ngettext(
            '%d slots was set to FALSE.',
            '%d slots were set to FALSE status',
            updated,
        ) % updated, messages.SUCCESS)

    model = Slot
    list_display = [
        'name',
        'abbreviation',
        'id_code',
        'op',
        'hour_start',
        'hour_end',
    ]
    actions = (move_to_op_TRUE, move_to_op_FALSE)


@admin.register(ShiftID)
class ShiftIDAdmin(admin.ModelAdmin):
    model = ShiftID
    list_display = [
        'label',
        'date_created'
    ]
    ordering = ('-label',)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):

    def MOVE_to_newest_VALID_revision(self, request, queryset):
        last_season = Revision.objects.filter(valid=True).order_by('-number').first()
        updated = queryset.update(revision=last_season)
        self.message_user(request, ngettext(
            '%d moved to the latest revision.',
            '%d moved to the latest revision',
            updated,
        ) % updated, messages.SUCCESS)
        self.description = 'Move selected shifts to the latest revision'

    def COPY_to_newest_TEMP_revision(self, request, queryset):
        last_rev = Revision.objects.order_by('-number').first()
        # updated = queryset.update(revision=last_rev)
        for one in queryset:
            _copy_shift(one, last_rev)
        self.description = 'Copy selected shifts to the latest temp revision'

    def MERGE_to_newest_VALID_revision(self, request, queryset):
        last_rev = Revision.objects.filter(valid=True).order_by('-number').first()
        for one in queryset:
            _copy_shift(one, last_rev)
        self.description = 'Merge back selected shifts to the latest valid revision'

    def UPDATE_to_default_slot_NWH(self, request, queryset):
        slot = Slot.objects.filter(abbreviation='NWH').first()
        # TODO consider changing mode to include 'default' field
        updated = queryset.update(slot=slot)
        self.message_user(request, ngettext(
            '%d moved to default slot (NWH).',
            '%d moved to default slot (NWH)',
            updated,
        ) % updated, messages.SUCCESS)
        self.description = 'Move selected shifts to default slot (NWH)'

    model = Shift
    list_display = [
        'date',
        'slot',
        '_member',
        'role',
        'revision',
        'shiftID',
    ]

    list_filter = ('campaign', 'revision', 'csv_upload_tag', 'slot', 'member__team', 'member__role', 'role', 'member')
    ordering = ('-date',)
    actions = (UPDATE_to_default_slot_NWH,
               MOVE_to_newest_VALID_revision,
               MERGE_to_newest_VALID_revision,
               COPY_to_newest_TEMP_revision)

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


def _copy_shift(oldShift, last_rev):
    shift = Shift()
    shift.campaign = oldShift.campaign
    shift.role = oldShift.role
    shift.revision = last_rev
    shift.date = oldShift.date
    shift.slot = oldShift.slot
    shift.member = oldShift.member
    shift.csv_upload_tag = oldShift.csv_upload_tag
    shift.save()
    return shift
