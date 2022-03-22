from django.contrib import admin
from assets.models import AssetBooking, Asset, AssetType


@admin.register(AssetBooking)
class AssetBooking(admin.ModelAdmin):
    model = Asset
    list_display = [
        'member',
        'asset',
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
    list_filter = ('state', 'asset__asset_type', 'asset', 'member__team')


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    model = Asset
    list_display = ['name', 'asset_type']
    list_filter = ('asset_type', )


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    model = AssetType
    list_display = ['name', 'description']
