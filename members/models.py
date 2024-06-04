from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.urls import reverse

class Team(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        permissions = (
            ('view_desiderata', 'View Desiderata'),
        )

    def search_display(self):
        return self.name

    def search_url(self):
        return reverse('team_view', kwargs={"team_id": self.id})


class Role(models.Model):
    name = models.CharField(max_length=200)
    priority = models.IntegerField(blank=True, default=99)
    abbreviation = models.CharField(max_length=10, default='OP')

    def __str__(self):
        return '{}'.format(self.name)


class Member(AbstractUser):
    class Meta:
        ordering = ['last_name']

    email = models.EmailField(_('New email address'), blank=True, null=True,
                              help_text=_('Set if the user has requested to change their email '
                                          'address but has not yet confirmed it.'))
    mobile = models.CharField(max_length=12, blank=True, default=None, null=True)
    team = models.ForeignKey(Team, blank=True, null=True,
                             on_delete=models.SET_NULL)
    role = models.ForeignKey(Role, blank=True, null=True,
                             on_delete=models.SET_NULL)
    line_manager = models.ForeignKey('self', blank=True, null=True,
                                     on_delete=models.SET_NULL)
    comments = models.TextField(max_length=10000, blank=True, default='')

    photo = models.TextField(max_length=10000, blank=True, null=True)
    notification_shifts = models.BooleanField(default=True, null=False)
    notification_studies = models.BooleanField(default=True, null=False)

    @cached_property
    def name(self):
        if self.last_name:
            return f'{self.first_name} {self.last_name}'
        else:
            return f'{self.first_name}'

    def __str__(self):
        return '{}'.format(self.name)

    def search_display(self):
        return "User: " + self.name

    def search_url(self):
        return reverse('users') + f"?u={self.id}"
