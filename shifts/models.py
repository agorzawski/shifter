from django.db import models
from django.db.models import DO_NOTHING, CASCADE

from members.models import Member
from django.utils import timezone
from django.utils.functional import cached_property
from django.shortcuts import reverse
import datetime
from enum import Enum

SIMPLE_DATE = "%Y-%m-%d"
SIMPLE_TIME = "%H:%M:%S"
DATE_FORMAT_FULL = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = '%Y-%m-%d'
DATE_FORMAT_SLIM = '%Y%m%d'
MONTH_NAME = '%B'


class Contact(models.Model):
    class ContactType(models.TextChoices):
        MAIL = 'email', 'Email'
        PHONE = 'phone', 'Phone Number'
        LINK = 'link', 'URL'
        ZOOM = 'zoom', 'Zoom Link'

    name = models.CharField(max_length=15)
    contact_type = models.CharField(
        max_length=5,
        choices=ContactType.choices,
        default=ContactType.PHONE,
    )
    contact = models.CharField(max_length=100)
    active = models.BooleanField(default=False)
    fa_icon = models.CharField(max_length=50, default='fa-phone')

    class Meta:
        verbose_name = "Contact"
        ordering = ['id']

    def __str__(self):
        if self.contact_type == 'email':
            return f"mailto:{self.contact}"
        elif self.contact_type == 'phone':
            return f"tel:{self.contact}"
        elif self.contact_type == 'link':
            return self.contact
        elif self.contact_type == 'zoom':
            return self.contact
        else:
            return ""

    def search_display(self):
        return "Contact: " + self.name

    def search_url(self):
        return str(self)


class ShifterMessage(models.Model):
    number = models.AutoField(primary_key=True, blank=True)
    description = models.TextField()
    valid = models.BooleanField(default=False)


class Revision(models.Model):
    number = models.AutoField(primary_key=True, blank=True)
    date_start = models.DateTimeField(null=False)
    valid = models.BooleanField()
    name = models.CharField(max_length=200, default='Default')
    merged = models.BooleanField(default=False)
    ready_for_preview = models.BooleanField(default=False)

    def __str__(self):
        return 'v{} {}'.format(self.number, self.name)


class Campaign(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date_start = models.DateField()
    date_end = models.DateField()
    revision = models.ForeignKey(Revision, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '{}'.format(self.name)

    @cached_property
    def full_details(self):
        return '{} from {} to {} at revision {} (currently {})'.format(self.name,
                                                                       self.date_start,
                                                                       self.date_end,
                                                                       self.revision, self.revision.valid)

    @cached_property
    def start_text(self):
        return self.date_start.strftime(SIMPLE_DATE)  # %H:%M:%S

    @cached_property
    def end_text(self):
        return self.date_end.strftime(SIMPLE_DATE)


class Slot(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(unique=True, max_length=10, default='AM')
    id_code = models.CharField(max_length=1, default='A')
    hour_start = models.TimeField(blank=False)
    hour_end = models.TimeField(blank=False)
    color_in_calendar = models.CharField(max_length=7, default='#0000FF')
    op = models.BooleanField(default=False)
    used_for_lookup = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({} - {})'.format(self.name, self.hour_start, self.hour_end)


class ShiftRole(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=10, default=None)
    priority = models.IntegerField(blank=True, default=99)
    color_in_calendar = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return '{}'.format(self.name)


class ShiftID(models.Model):
    label = models.CharField(max_length=9, )
    date_created = models.DateTimeField(null=False)

    def __str__(self):
        return '{}'.format(self.label)


class Desiderata(models.Model):
    """
    A Desiderata belongs to a user. By default, a desireta represent a time slot where the user IS NOT available.
    """

    class DesiderataType(models.TextChoices):
        VACATION = 'vac', 'Vacation'
        CONFERENCE = 'conf', 'Conference'
        OTHER = 'other', 'Other'

    start = models.DateTimeField()
    stop = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    member = models.ForeignKey(Member, on_delete=CASCADE)
    type = models.CharField(
        max_length=10,
        choices=DesiderataType.choices,
        default=DesiderataType.VACATION,
    )

    def get_as_json_event(self, team=False, editable=True):
        event = {'id': self.id,
                 'start': timezone.localtime(self.start).strftime(format=DATE_FORMAT_FULL),
                 'end': timezone.localtime(self.stop).strftime(format=DATE_FORMAT_FULL),
                 'allDay': self.all_day,
                 }

        if self.type == 'vac':
            event['color'] = '#ab4646'
            event['title'] = "Vacation (All day)" if self.all_day else "Vacation"
        elif self.type == 'conf':
            event['color'] = '#638ef2'
            event['title'] = "Conference (All day)" if self.all_day else "Conference"
        else:
            event['color'] = '#8ff29c'
            event['title'] = "Unavailable (All day)" if self.all_day else "Unavailable"
        if team:
            event['title'] = self.member.name + " - " + event['title']

        if not editable:
            event['editable'] = False
            event['color'] = '#fcba03'
        return event


class Shift(models.Model):
    class Moment(Enum):
        START = 0
        END = 1

    campaign = models.ForeignKey(Campaign, on_delete=DO_NOTHING)
    date = models.DateField()
    slot = models.ForeignKey(Slot, on_delete=DO_NOTHING)
    member = models.ForeignKey(Member, on_delete=DO_NOTHING)
    revision = models.ForeignKey(Revision, on_delete=DO_NOTHING)
    shiftID = models.ForeignKey(ShiftID, on_delete=DO_NOTHING, null=True, blank=True, )

    role = models.ForeignKey(ShiftRole, blank=True, null=True, on_delete=DO_NOTHING)
    csv_upload_tag = models.CharField(max_length=200, blank=True, null=True, )

    is_cancelled = models.BooleanField(default=False, help_text='Last minute cancellation? IT IS counted for the HR '
                                                                'code.')
    is_active = models.BooleanField(default=True, help_text='Leave or early cancellation, IT IS NOT counted for the '
                                                            'HR code.')

    pre_comment = models.TextField(blank=True, null=True,
                                   help_text='Text to be displayed in shifters as shift constraint. [Shifters view '
                                             'ONLY]')
    post_comment = models.TextField(blank=True, null=True,
                                    help_text='Summary/comment for the end/post shift time. [Shifters view ONLY]')

    class Meta:
        unique_together = (("date", "slot", "member", "role", "campaign", "revision"),)

    def __str__(self):
        return '{} {} {}'.format(self.member, self.date, self.slot)

    def get_shift_as_date_slot(self) -> str:
        return '{} {}'.format( self.date, self.slot)

    def get_shift_title(self) -> str:
        title = f"{self.member.first_name} as "
        if not self.is_active or self.is_cancelled:
            return f"INACTIVE {self.member.first_name}"
        if self.role:
            title += f"{self.role} ({self.member.role})"
        else:
            title += f"{self.member.role}"

        return title

    def get_color_for_calendar(self):
        if not self.is_active or self.is_cancelled:
            return '#EDEDED'
        if self.role is not None and self.role.color_in_calendar is not None:
            return self.role.color_in_calendar
        return self.slot.color_in_calendar

    def get_shift_as_json_event(self) -> dict:
        event = {'id': self.id,
                 'title': self.get_shift_title(),
                 'start': self.get_proper_times(self.Moment.START).strftime(format=DATE_FORMAT_FULL),
                 'end': self.get_proper_times(self.Moment.END).strftime(format=DATE_FORMAT_FULL),
                 'url': reverse('shifter:users') + f'?u={self.member.id}',
                 'slot': self.slot.name,
                 'pre_comment': self.pre_comment,
                 'post_comment': self.post_comment,
                 'color': self.get_color_for_calendar(),
                 }
        if 'ShiftLeader' in self.member.role.name:
            event['textColor'] = '#E9E72D'
        if not self.is_active or self.is_cancelled:
            event['textColor'] = '#BDBDBD'
        return event

    def get_planned_shift_as_json_event(self) -> dict:
        event = {'id': self.id,
                 'title': self.get_shift_title(),
                 'start': self.get_proper_times(self.Moment.START).strftime(format=DATE_FORMAT_FULL),
                 'end': self.get_proper_times(self.Moment.END).strftime(format=DATE_FORMAT_FULL),
                 'url': reverse('shifter:users') + f'?u={self.member.id}',
                 'slot': self.slot.name,
                 'pre_comment': self.pre_comment,
                 'post_comment': self.post_comment,
                 'color': self.get_color_for_calendar(),
                 'borderColor': 'black',
                 'textColor': 'black',
                 }
        return event

    def get_simplified_as_json(self):
        return {'id': self.id, 'title': self.__str__()}

    @cached_property
    def start(self) -> datetime:
        return self.get_proper_times(self.Moment.START)

    @cached_property
    def end(self) -> datetime:
        return self.get_proper_times(self.Moment.END)

    @cached_property
    def shift_start(self) -> str:
        return self.get_proper_times(self.Moment.START).strftime(DATE_FORMAT_FULL)

    @cached_property
    def shift_end(self) -> str:
        return self.get_proper_times(self.Moment.END).strftime(DATE_FORMAT_FULL)

    def get_proper_times(self, moment) -> datetime:
        timeToUse = self.slot.hour_start
        if moment == self.Moment.END:
            timeToUse = self.slot.hour_end
        deltaToAdd = 0
        diff = datetime.datetime.combine(self.date, self.slot.hour_start) - datetime.datetime.combine(self.date,
                                                                                                      self.slot.hour_end)
        if diff > datetime.timedelta(minutes=0) and moment == self.Moment.END:
            deltaToAdd = 1
        return datetime.datetime.combine(self.date, timeToUse) + datetime.timedelta(days=deltaToAdd)


class ShiftExchangePair(models.Model):
    shift = models.ForeignKey(Shift, on_delete=DO_NOTHING)
    shift_for_exchange = models.ForeignKey(Shift, on_delete=DO_NOTHING, related_name='for_exchange')

    def __str__(self):
        return '[OLD] {} on {} {} for [NEW] {} on {} {}'.format(self.shift.member,
                                                          self.shift.date,
                                                          self.shift.slot.abbreviation,
                                                          self.shift_for_exchange.member,
                                                          self.shift_for_exchange.date,
                                                          self.shift_for_exchange.slot.abbreviation, )


class ShiftExchange(models.Model):
    requestor = models.ForeignKey(Member, on_delete=DO_NOTHING)
    requested = models.DateTimeField()
    tentative = models.BooleanField(default=True)
    approver = models.ForeignKey(Member, blank=True, null=True, on_delete=DO_NOTHING, related_name='approver')
    approved = models.DateTimeField(blank=True, null=True, )

    shifts = models.ManyToManyField(ShiftExchangePair, blank=True)
    applicable = models.BooleanField(default=False)
    backupRevision = models.ForeignKey(Revision, on_delete=DO_NOTHING, related_name='revision')
    implemented = models.BooleanField(default=False)

    def __str__(self):
        return '{} on {} for {} shifts swap; implemented:{}'.format(self.requestor,
                                                                    self.requested.strftime(SIMPLE_DATE),
                                                                    self.shifts.all().count(),
                                                                    self.implemented)

    @cached_property
    def requested_date(self) -> str:
        return self.requested.strftime(DATE_FORMAT_FULL)

    @cached_property
    def approved_date(self) -> str:
        return self.approved.strftime(DATE_FORMAT_FULL)

