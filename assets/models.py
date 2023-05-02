from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from members.models import Member
from django.urls import reverse

class AssetType(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    def __str__(self):
        return '{}'.format(self.name)


class Asset(models.Model):
    name = models.CharField(max_length=200)
    asset_type = models.ForeignKey(AssetType, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '{} | {}'.format(self.asset_type.name, self.name)

    def search_display(self):
        return "Asset: " + str(self)

    def search_url(self):
        return reverse('assets')


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

    def asset_as_json(self, user=None):
        data = {'who': {'member': f'{self.member}', 'team': f'{self.member.team}'},
                'asset': {'type': f'{self.asset.asset_type.name}', 'name': f'{self.asset.name}'},
                'use_start': {'display': timezone.localtime(self.use_start).strftime('%b. %d, %Y, %I:%M%p'),
                              'order': self.use_start.timestamp()},
                'use_end': {'display': timezone.localtime(self.use_end).strftime('%b. %d, %Y, %I:%M%p'),
                            'order': self.use_end.timestamp()},
                'active': "Active" if self.state != AssetBooking.BookingState.RETURNED else "Over",
                'comment': f'<small> {timezone.localtime(self.booking_created).strftime("%b. %d, %Y, %I:%M%p")} / {self.booked_by}'
                           f'</small><br> {self.initial_comment}'}
        if self.state == 'R':
            data['closing'] = f"<span class='badge bg-success'>Booking over</span> <br>{self.booking_finished.strftime('%b. %d, %Y, %I:%M%p')}<br>{self.finished_by}<br>{self.after_comment}"
        else:
            if self.member != user and not user.is_staff:
                data['closing'] = '<span class="badge bg-warning">Booking ongoing</span>'
            else:
                data['closing'] = f"<a class='btn btn-outline-success' data-book_id={self.id} data-name='{self.asset.asset_type.name} - {self.asset.name}' onclick='test(event)'> End booking </a>"
        return data

    def search_display(self):
        return "Asset booking: " + str(self)

    def search_url(self):
        return reverse('assets')