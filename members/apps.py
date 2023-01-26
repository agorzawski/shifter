from django.apps import AppConfig
from watson import search as watson


class MembersConfig(AppConfig):
    name = 'members'

    def ready(self):
        team = self.get_model("Team")
        watson.register(team)
        member = self.get_model("Member")
        watson.register(member)
