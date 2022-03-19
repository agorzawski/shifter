from django.db import models
from django.utils.translation import gettext_lazy as _
from members.models import Member


class AssetType(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    def __str__(self):
        return '{}'.format(self.name)


class Asset(models.Model):
    name = models.CharField(max_length=200)
    asset_type = models.ForeignKey(AssetType, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '{} | {}'.format( self.asset_type.name, self.name)


class AssetBooking(models.Model):
    member = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL, related_name='using_member')
    booked_by = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL, related_name='booking_member')
    finished_by = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, related_name='closing_member')

    asset = models.ForeignKey(Asset, blank=False, null=True, on_delete=models.SET_NULL)

    class BookingState(models.TextChoices):
        BOOKED = 'B', _('Booked')
        RETURNED = 'R', _('Returned')
        INUSE = 'U', _('In Use')

    state = models.CharField(max_length=1,
                             choices=BookingState.choices,
                             default=BookingState.BOOKED,)

    use_start = models.DateTimeField(blank=False)
    use_end = models.DateTimeField(blank=False)
    initial_comment = models.TextField(max_length=2000, blank=True, default=None, null=True)
    booking_created = models.DateTimeField(blank=False)
    booking_finished = models.DateTimeField(blank=True, null=True, )
    after_comment = models.TextField(max_length=2000, blank=True, default=None, null=True)

    def __str__(self):
        return '{} ({}) for {}'.format(self.member, self.asset, self.use_start)