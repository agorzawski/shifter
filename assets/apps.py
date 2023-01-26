from django.apps import AppConfig
from watson import search as watson


class AssetsConfig(AppConfig):
    name = 'assets'

    def ready(self):
        asset = self.get_model("Asset")
        watson.register(asset)
        booking = self.get_model("AssetBooking")
        watson.register(booking)
