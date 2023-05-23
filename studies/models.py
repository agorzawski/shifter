from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.utils import timezone
from django.db.models import DO_NOTHING
import datetime
from members.models import Member
from enum import Enum
from django.urls import reverse

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
        ('P', 'Planned'),
        ('R', 'Requested'),
        ('B', 'Booked'),
        ('C', 'Canceled'),
        ('D', 'Done'),
    ]

    member = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL, related_name='study_using_member')
    collaborators = models.ManyToManyField(Member, blank=True)
    booked_by = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL, related_name='study_booking_member')
    finished_by = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='study_closing_member')


    #Study variables
    title = models.CharField(max_length=200, blank=False, null=False, help_text='Title')
    description = models.TextField(max_length=2000, blank=True, null=True, help_text='Study Description')
    booking_comment = models.TextField(max_length=2000, blank=True, null=True, help_text='Comment regarding time slot')
    beam_current = models.FloatField(default=6.0, blank=True, null=True, help_text='Max. Beam Current (mA)')
    beam_pulse_length = models.FloatField(default=5.0, blank=True, null=True, help_text='Max. Beam Pulse Length (us)')
    beam_destination = models.CharField(default='LEBT', choices=BEAM_DESTINATION_CHOICES, blank=True, null=True, max_length=200, help_text='Beam Destination')
    beam_reprate = models.IntegerField(default=1, choices=REP_RATE_CHOICES, blank=True, null=True,
                                       help_text='Max. beam repetition rate (Hz)')
    jira = models.URLField(blank=True, null=True, help_text='Add a JIRA link (or any other link connect to the study) if possible')
    duration = models.IntegerField(default=1, choices=STUDY_DURANTION_CHOICES, null=False, blank=False, help_text='Study duration (30 min steps)')

    #Admin variables
    slot_start = models.DateTimeField(default=datetime.datetime.now)
    slot_end = models.DateTimeField(default=datetime.datetime.now)
    priority = models.BooleanField(default=False)

    state = models.CharField(max_length=1,
                             choices=BOOKING_STATE_CHOICES,
                             default='P', )

    booking_created = models.DateTimeField(blank=False)
    booking_finished = models.DateTimeField(blank=True, null=True, )
    after_comment = models.TextField(max_length=2000, blank=True, default=None, null=True)
    logbook_link = models.URLField(blank=True, null=True, help_text='Add an logbook link with study summary if possible')

    def search_display(self):
        return "Study: " + self.title

    def search_url(self):
        return reverse('studies:study_request')

    def state_badge(self):
        if self.state == 'R':
            return '<span class="badge text-bg-primary">Requested</span>'
        elif self.state == 'B':
            return '<span class="badge text-bg-warning">Booked</span>'
        elif self.state == 'C':
            return '<span class="badge text-bg-secondary">Canceled</span>'
        elif self.state == 'D':
            return '<span class="badge text-bg-success">Done</span>'
        elif self.state == 'P':
            return '<span class="badge text-bg-primary">Planned</span>'
        else:
            return '<span class="badge text-bg-info">Unknown</span>'

    def __str__(self):
        return '{}'.format(self.member)

    @cached_property
    def study_start(self) -> str:
        return timezone.localtime(self.slot_start).strftime(DATE_FORMAT_FULL)

    @cached_property
    def study_end(self) -> str:
        return timezone.localtime(self.slot_end).strftime(DATE_FORMAT_FULL)

    @cached_property
    def study_time_start(self) -> str:
        return timezone.localtime(self.slot_start).strftime(SIMPLE_TIME)

    @cached_property
    def study_time_end(self) -> str:
        return timezone.localtime(self.slot_end).strftime(SIMPLE_TIME)

    def get_study_as_json(self) -> dict:
        return {
            'title': self.title,
            'lead': self.member.name,
            'leadEmail': self.member.email,
            'leadPhone': self.member.mobile,
            'team': [m.name for m in self.collaborators.all()],
            'start': self.study_start,
            'end': self.study_end,
        }

    def get_study_as_json_event(self) -> dict:
        event = {'id': self.id,
                 'title': self.member.first_name + ' for ' + self.title,
                 'start': self.study_start,
                 'end': self.study_end,
                 'color': '#F5D959',
                 'textColor': '#FF3333' if self.priority else '#676767',
                 'borderColor': '#FF3333' if self.priority else '#BBBBBB'
        }
        return event

    def study_as_datatable_json(self, user=None):
        data = {'id' : f'{self.id}',
                'who': {'member': f'{self.member}', 'team': f'{self.member.team}'},
                'collaborators': [f'{m}' for m in self.collaborators.all()],
                'title': self.title,
                'description': self.description,
                'request_start': {'display': timezone.localtime(self.slot_start).strftime('%b. %d, %Y, %I:%M%p'), 'order': self.slot_end.timestamp()},
                'request_end': {'display': timezone.localtime(self.slot_end).strftime('%b. %d, %Y, %I:%M%p'), 'order': self.slot_end.timestamp()},
                'state': {'order': [tup for tup in self.BOOKING_STATE_CHOICES if tup[0] == self.state][0][1],
                          'display': ''},
                'booking': 'pass'}
        data['state']['display'] = self.state_badge()
        if self.state == 'D' or self.state == 'C':
            if self.logbook_link is None or not bool(self.logbook_link.strip()):
                data['booking'] = f"<span class='badge bg-secondary'>Study request closed</span> <br>{self.booking_finished.strftime('%b. %d, %Y, %I:%M%p')}<br>{self.finished_by}<br>{self.after_comment}<br>"
            else:
                data['booking'] = f"<span class='badge bg-secondary'>Study request closed</span> <br>{self.booking_finished.strftime('%b. %d, %Y, %I:%M%p')}<br>{self.finished_by}<br>{self.after_comment}<br><a href={self.logbook_link}>Logbook Link</a>"
        else:
            if self.member != user and not user.is_staff:
                data['booking'] = data['state']['display']
            else:
                data['booking'] = f"<a class='btn btn-outline-dark' data-book_id={self.id} data-name='{self.title}' onclick='test(event)'> Edit study request</a>"
        return data
