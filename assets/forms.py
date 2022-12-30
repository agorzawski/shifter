from django import forms
from django.forms import ValidationError
from django.forms.widgets import HiddenInput
from .models import *

from assets.models import AssetBooking
from members.models import Member


class AssetBookingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(AssetBookingForm, self).__init__(*args, **kwargs)
        if self.user.is_staff:
            self.fields['member'].choices = [(x.id, x.name) for x in Member.objects.all()]
        else:
            self.fields['member'].choices = [(x.id, x.name) for x in [self.user]]

    class Meta:
        model = AssetBooking
        fields = ('member', 'asset', 'use_start', 'use_end', 'initial_comment')


class AssetBookingFormClosing(forms.Form):
    booking_id = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'closed_booking_id_to_set',}))
    after_comment = forms.CharField(widget=forms.Textarea)


