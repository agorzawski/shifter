from django.apps import AppConfig
from watson import search as watson


class StudiesConfig(AppConfig):
    name = 'studies'

    def ready(self):
        study = self.get_model("StudyRequest")
        watson.register(study)
