from django.db import models
from django.db.models import DO_NOTHING

from members.models import Member
from django.utils.functional import cached_property
import datetime
from enum import Enum

SIMPLE_DATE = "%Y-%m-%d"


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


class Shift(models.Model):

    class Moment(Enum):
        START = 0
        END = 1

    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    campaign = models.ForeignKey(Campaign, on_delete=DO_NOTHING)
    date = models.DateField()
    slot = models.ForeignKey(Slot, on_delete=DO_NOTHING)
    member = models.ForeignKey(Member, on_delete=DO_NOTHING)
    revision = models.ForeignKey(Revision, on_delete=DO_NOTHING)

    role = models.ForeignKey(ShiftRole, blank=True, null=True, on_delete=DO_NOTHING)
    csv_upload_tag = models.CharField(max_length=200, blank=True, null=True,)

    class Meta:
        unique_together = (("date", "slot", "member", "role", "campaign", "revision"),)

    def __str__(self):
        return '{} {} {}'.format(self.member, self.date, self.slot)

    @cached_property
    def start(self) -> datetime:
        return self.get_proper_times(self.Moment.START)

    @cached_property
    def end(self) -> datetime:
        return self.get_proper_times(self.Moment.END)

    @cached_property
    def shift_start(self) -> str:
        return self.get_proper_times(self.Moment.START).strftime(self.DATE_FORMAT)

    @cached_property
    def shift_end(self) -> str:
        return self.get_proper_times(self.Moment.END).strftime(self.DATE_FORMAT)

    def get_proper_times(self, moment) -> datetime:
        timeToUse = self.slot.hour_start
        if moment == self.Moment.END:
            timeToUse = self.slot.hour_end
        deltaToAdd = 0
        diff = datetime.datetime.combine(self.date, self.slot.hour_start) - datetime.datetime.combine(self.date, self.slot.hour_end)
        if diff > datetime.timedelta(minutes=0) and moment == self.Moment.END:
            deltaToAdd = 1
        return datetime.datetime.combine(self.date, timeToUse) + datetime.timedelta(days=deltaToAdd)