from django import forms
from django.forms import ValidationError
from .models import *

from assets.models import AssetBooking


class AssetBookingForm(forms.ModelForm):
    class Meta:
        model = AssetBooking
        fields = ('member', 'asset', 'use_start', 'use_end', 'initial_comment')


class AssetBookingFormClosing(forms.ModelForm):
    class Meta:
        model = AssetBooking
        fields = ('after_comment',)

