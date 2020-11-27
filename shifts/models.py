from django.db import models
from members.models import Member


class Campaign(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()


class Slot(models.Model):
    name = models.CharField(max_length=200)
    hour_start =  models.IntegerField()
    hour_end = models.IntegerField()


class Shift(models.Model):
    date = models.DateField()
    slot = models.ForeignKey(Slot, blank=True, null=True,
                            on_delete=models.SET_NULL)
    member = models.ForeignKey(Member, blank=True, null=True,
                            on_delete=models.SET_NULL)
