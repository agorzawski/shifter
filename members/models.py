from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _


class Team(models.Model):
    name = models.CharField(max_length=200)


class Member(AbstractUser):
    class Meta:
        ordering = ['last_name']

    email = models.EmailField(_('New email address'), blank=True, null=True,
                                  help_text=_('Set if the user has requested to change their email address but has not yet confirmed it.'))
    mobile = models.CharField(max_length=12, blank=True, default=None, null=True)
    lineManager = models.ManyToManyField("self")
    teams = models.ManyToManyField(Team, blank=True)
