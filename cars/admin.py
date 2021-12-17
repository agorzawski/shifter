from django.contrib import admin
from cars.models import VehicleBooking, Vehicle


@admin.register(VehicleBooking)
class VehicleBooking(admin.ModelAdmin):
    model = Vehicle
    list_display = [
        'member',
        'vehicle',
        'state',
        'use_start',
        'use_end',
        'initial_comment',
        'booking_created',
        'booked_by',
        'finished_by',
        'booking_finished',
        'after_comment'
    ]
    list_filter = ('state', 'vehicle', 'member__team')


@admin.register(Vehicle)
class CarAdmin(admin.ModelAdmin):
    model = Vehicle
    list_display = ['name', 'license_plate']
