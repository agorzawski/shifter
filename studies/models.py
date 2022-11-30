from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.db.models import DO_NOTHING
import datetime
from members.models import Member
from enum import Enum

SIMPLE_DATE = "%Y-%m-%d"
SIMPLE_TIME = "%H:%M"
DATE_FORMAT_FULL = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = '%Y-%m-%d'
DATE_FORMAT_SLIM = '%Y%m%d'
MONTH_NAME = '%B'


#class PulseLength(models.Model):
#    name = models.CharField(max_length=200)
#    description = models.CharField(max_length=200)

#    def __str__(self):
#        return '{}'.format(self.name)


#class BeamDestination(models.Model):
#    name = models.CharField(max_length=200)
#    description = models.CharField(max_length=200)

#    def __str__(self):
#        return '{}'.format(self.name)


#class Duration(models.Model):
#    name = models.CharField(max_length=200)
#    description = models.CharField(max_length=200)

#    def __str__(self):
#        return '{}'.format(self.name)


#class StudySlot(models.Model):
#    name = models.CharField(max_length=200)
#    abbreviation = models.CharField(max_length=10, default='AM')
#    id_code = models.CharField(max_length=1, default='A')
#    hour_start = models.TimeField(blank=True, null=True,)
#    hour_end = models.TimeField(blank=True, null=True,)
#    color_in_calendar = models.CharField(max_length=7, default='#0000FF')

#    def __str__(self):
#        return '{} ({} - {})'.format(self.name, self.hour_start, self.hour_end)


#class BeamParameters(models.Model):
#    BEAM_DESTINATION_CHOICES = [
#        ('LEBT', 'LEBT FC'),
#        ('MEBT', 'MEBT FC'),
#        ('DTL2', 'DTL2 FC'),
#        ('DTL4', 'DTL4 FC'),
#        ('OTHER', 'OTHER'),
#    ]

#    STUDY_DURANTION_CHOICES = [
#        (1, '30 min'),
#        (2, '60 min'),
#        (3, '1.5 hour'),
#        (4, '2.0 hours'),
#        (5, '2.5 hours'),
#        (6, '3 hours'),
#        (7, 'more than 3 hours'),
#    ]

#    REP_RATE_CHOICES = [
#        (1, '1 Hz'),
#        (2, '2 Hz'),
#        (3, '3.5 Hz'),
#        (7, '7 Hz'),
#        (14, '14 Hz'),
#        (10, 'Uneven rate'),
#    ]

#    beam_current = models.FloatField(default=6.0, blank=True, null=True, help_text='Max. Beam Current (mA)')
#    beam_pulse_length = models.FloatField(default=5.0, blank=True, null=True, help_text='Max. Beam Pulse Length (us)')
#    beam_destination = models.CharField(default='LEBT', choices=BEAM_DESTINATION_CHOICES, blank=True, null=True,
#                                        max_length=200, help_text='Beam Destination')
#    beam_reprate = models.CharField(default='14 Hz', choices=REP_RATE_CHOICES, blank=True, null=True,
#                                        max_length=200, help_text='Max. beam repetition rate (Hz)')
#    special_beam_requirements = models.TextField(max_length=2000, blank=True, null=True, help_text='Special Beam requirements')


#class Collaborators(models.Model):
#    name = models.CharField(max_length=128)
#    members = models.ManyToManyField(
#        Member,
#        through='StudyRequest',
#        through_fields=('collaborators', 'member'),
#    )


class StudyRequest(models.Model):

    BEAM_DESTINATION_CHOICES = [
        ('LEBT', 'LEBT FC'),
        ('MEBT', 'MEBT FC'),
        ('DTL2', 'DTL2 FC'),
        ('DTL4', 'DTL4 FC'),
        ('OTHER', 'OTHER'),
    ]

    STUDY_DURANTION_CHOICES = [
        (1, '30 min'),
        (2, '60 min'),
        (3, '1.5 hour'),
        (4, '2.0 hours'),
        (5, '2.5 hours'),
        (6, '3 hours'),
        (7, 'more than 3 hours'),
    ]

    REP_RATE_CHOICES = [
        (1, '1 Hz'),
        (2, '2 Hz'),
        (3, '3.5 Hz'),
        (4, '7 Hz'),
        (5, '14 Hz'),
        (6, 'Uneven rate'),
    ]

    BOOKING_STATE_CHOICES = [
        ('R', 'Requested'),
        ('B', 'Booked'),
        ('C', 'Canceled'),
        ('D', 'Done'),
    ]

    member = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL, related_name='study_using_member',help_text='study leader')
    booked_by = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL, related_name='study_booking_member')
    finished_by = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='study_closing_member')

    #collaborators = models.ForeignKey(Collaborators, null=True, on_delete=models.SET_NULL, help_text='study collaborators')

    #Study variables
    title = models.CharField(max_length=200, blank=True, null=True, help_text='Title')
    description = models.TextField(max_length=2000, blank=True, null=True, help_text='Study Description')
    beam_current = models.FloatField(default=6.0, blank=True, null=True, help_text='Max. Beam Current (mA)')
    beam_pulse_length = models.FloatField(default=5.0, blank=True, null=True, help_text='Max. Beam Pulse Length (us)')
    beam_destination = models.CharField(default='LEBT', choices=BEAM_DESTINATION_CHOICES, blank=True, null=True, max_length=200, help_text='Beam Destination')
    beam_reprate = models.IntegerField(default=1, choices=REP_RATE_CHOICES, blank=True, null=True,
                                     help_text='Max. beam repetition rate (Hz)')
    jira = models.URLField(blank=True, null=True,help_text='Add a JIRA link if possible')
    duration = models.IntegerField(default=1,choices=STUDY_DURANTION_CHOICES, null=True, blank=True, help_text='Study duration (30 min steps)')

    #Admin variables
    slot_start = models.DateTimeField(default=datetime.datetime.now())
    slot_end = models.DateTimeField(default=datetime.datetime.now())
    priority = models.BooleanField(default=False)

    state = models.CharField(max_length=1,
                             choices=BOOKING_STATE_CHOICES,
                             default='R', )

    booking_created = models.DateTimeField(blank=False)
    booking_finished = models.DateTimeField(blank=True, null=True, )
    after_comment = models.TextField(max_length=2000, blank=True, default=None, null=True)

    def __str__(self):
        return '{}'.format(self.member)

    @cached_property
    def study_start(self) -> str:
        return self.slot_start.strftime(DATE_FORMAT_FULL)

    @cached_property
    def study_end(self) -> str:
        return self.slot_end.strftime(DATE_FORMAT_FULL)

    @cached_property
    def study_time_start(self) -> str:
        return self.slot_start.strftime(SIMPLE_TIME)

    @cached_property
    def study_time_end(self) -> str:
        return self.slot_end.strftime(SIMPLE_TIME)