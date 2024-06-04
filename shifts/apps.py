from django.apps import AppConfig
from watson import search as watson


class ShiftsConfig(AppConfig):
    name = 'shifts'

    def ready(self):
        contacts = self.get_model("Contact")
        watson.register(contacts)
        import shifts.signals

