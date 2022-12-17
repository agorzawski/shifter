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


class ShifterMessage(models.Model):
    number = models.AutoField(primary_key=True, blank=True)
    description = models.TextField()
    valid = models.BooleanField(default=False)


class Revision(models.Model):
    number = models.AutoField(primary_key=True, blank=True)
    date_start = models.DateTimeField(null=False)
    valid = models.BooleanField()

    def __str__(self):
        return 'v{} from {}'.format(self.number, self.date_start.strftime(SIMPLE_DATE))


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
        return self.date_start.strftime(SIMPLE_DATE) # %H:%M:%S

    @cached_property
    def end_text(self):
        return self.date_end.strftime(SIMPLE_DATE)


class Slot(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=10, default='AM')
    id_code = models.CharField(max_length=1, default='A')
    hour_start = models.TimeField(blank=False)
    hour_end = models.TimeField(blank=False)
    color_in_calendar = models.CharField(max_length=7, default='#0000FF')
    op = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({} - {})'.format(self.name, self.hour_start, self.hour_end)


class ShiftRole(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=10, default=None)
    priority = models.IntegerField(blank=True, default=99)

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
    start = models.DateTimeField()
    stop = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    member = models.ForeignKey(Member, on_delete=CASCADE)

    def get_as_json_event(self, team=False):
        event = {'id': self.id,
                 'title': "Unavailable (All day)" if self.all_day else "Unavailable",
                 'start': timezone.localtime(self.start).strftime(format=DATE_FORMAT_FULL),
                 'end': timezone.localtime(self.stop).strftime(format=DATE_FORMAT_FULL),
                 'allDay': self.all_day,
                 }
        if team:
            event['title'] = self.member.name + " " + event['title']
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
    shiftID = models.ForeignKey(ShiftID, on_delete=DO_NOTHING, null=True, blank=True,)

    role = models.ForeignKey(ShiftRole, blank=True, null=True, on_delete=DO_NOTHING)
    csv_upload_tag = models.CharField(max_length=200, blank=True, null=True,)

    class Meta:
        unique_together = (("date", "slot", "member", "role", "campaign", "revision"),)

    def __str__(self):
        return '{} {} {}'.format(self.member, self.date, self.slot)

    def get_shift_title(self) -> str:
        title = f"{self.member.first_name} as "
        if self.role:
            title += f"{self.role} ({self.member.role})"
        else:
            title += f"{self.member.role}"

        return title

    def get_shift_as_json_event(self) -> dict:
        event = {'id': self.id,
                 'title': self.get_shift_title(),
                 'start': self.get_proper_times(self.Moment.START).strftime(format=DATE_FORMAT_FULL),
                 'end': self.get_proper_times(self.Moment.END).strftime(format=DATE_FORMAT_FULL),
                 'url': reverse('shifter:user', args=(self.member.id,)),
                 'color': self.slot.color_in_calendar,
                 }
        if 'ShiftLeader' in self.member.role.name:
            event['textColor'] = '#E9E72D'
        return event

    def get_planned_shift_as_json_event(self) -> dict:
        event = {'id': self.id,
                 'title': self.get_shift_title(),
                 'start': self.get_proper_times(self.Moment.START).strftime(format=DATE_FORMAT_FULL),
                 'end': self.get_proper_times(self.Moment.END).strftime(format=DATE_FORMAT_FULL),
                 'url': reverse('shifter:user', args=(self.member.id,)),
                 'color': self.slot.color_in_calendar,
                 'borderColor': 'red',
                 'textColor':'red',
                 }
        return event

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
        diff = datetime.datetime.combine(self.date, self.slot.hour_start) - datetime.datetime.combine(self.date, self.slot.hour_end)
        if diff > datetime.timedelta(minutes=0) and moment == self.Moment.END:
            deltaToAdd = 1
        return datetime.datetime.combine(self.date, timeToUse) + datetime.timedelta(days=deltaToAdd)