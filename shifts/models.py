from django.db import models
from members.models import Member
from django.utils.functional import cached_property
from datetime  import datetime, time

class Campaign(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date_start = models.DateField()
    date_end = models.DateField()

    def __str__(self):
        return '{}'.format(self.name)


class Slot(models.Model):
    name = models.CharField(max_length=200)
    hour_start =  models.TimeField(blank=False)
    hour_end = models.TimeField(blank=False)

    def __str__(self):
        return '{} ({} - {})'.format(self.name, self.hour_start, self.hour_end)


class Shift(models.Model):

    campaign = models.ForeignKey(Campaign, blank=True, null=True,
                            on_delete=models.SET_NULL)
    date = models.DateField()
    slot = models.ForeignKey(Slot, blank=True, null=True,
                            on_delete=models.SET_NULL)
    member = models.ForeignKey(Member, blank=True, null=True,
                            on_delete=models.SET_NULL)
    def __str__(self):
        return '{} {} {}'.format(self.member, self.date, self.slot)

    @cached_property
    def shift_start(self):
        return datetime.combine(self.date, self.slot.hour_start).strftime("%Y-%m-%d %H:%M:%S")

    @cached_property
    def shift_end(self):
        return datetime.combine(self.date, self.slot.hour_end).strftime("%Y-%m-%d %H:%M:%S")
