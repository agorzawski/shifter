from django import forms
from django.forms import ValidationError
from .models import *

from cars.models import VehicleBooking


class VehicleBookingForm(forms.ModelForm):
    class Meta:
        model = VehicleBooking
        fields = ('member', 'vehicle', 'use_start', 'use_end', 'initial_comment')


class VehicleBookingFormClosing(forms.ModelForm):
    class Meta:
        model = VehicleBooking
        fields = ('after_comment',)

